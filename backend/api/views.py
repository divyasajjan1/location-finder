from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Landmark, LandmarkPrediction, LandmarkImage, TrainingRun, ChatMessage
from .serializers import LandmarkSerializer, TrainingRunSerializer

from api.utils.distance_to_landmark import distance_to_landmark
from api.utils.landmark_facts import get_landmark_facts
from api.utils.gemini_summary import generate_summary
from .predict import predict_image
import os
from django.conf import settings
from .scraping_service import scrape_images_for_landmark 
from .landmark_management import get_or_create_landmark 
from .train_landmarks import train_model
from google import genai
from django.db import transaction


class BulkImageUploadView(APIView):
    def post(self, request, *args, **kwargs):
        landmark_name = request.data.get('landmark_name')
        if not landmark_name:
            return Response({'error': 'Landmark name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Sanitize and verify the landmark exists in the DB
        landmark_name_sanitized = landmark_name.lower().replace(" ", "_")
        try:
            landmark_instance = Landmark.objects.get(name=landmark_name_sanitized)
        except Landmark.DoesNotExist:
            return Response({'error': f'Landmark "{landmark_name_sanitized}" not found in database. Please create it first.'}, status=status.HTTP_404_NOT_FOUND)

        # 2. Setup Directory
        upload_dir = os.path.join(settings.BASE_DIR.parent, 'data', 'raw', landmark_name_sanitized)
        os.makedirs(upload_dir, exist_ok=True)

        # 3. Determine naming convention (highest number + 1)
        uploaded_count = 0
        existing_files = os.listdir(upload_dir)
        highest_num = 0
        for fname in existing_files:
            try:
                name_without_ext = os.path.splitext(fname)[0]
                if name_without_ext.isdigit():
                    highest_num = max(highest_num, int(name_without_ext))
            except ValueError:
                pass
        
        next_image_idx = highest_num + 1

        # 4. Process Files
        for key, file_obj in request.FILES.items():
            if key.startswith('file'):
                try:
                    # Construct file system path
                    new_filename = f"{next_image_idx}.jpg"
                    file_path = os.path.join(upload_dir, new_filename)
                    
                    # Save physical file
                    with open(file_path, 'wb+') as destination:
                        for chunk in file_obj.chunks():
                            destination.write(chunk)

                    # 5. Create Database Entry for the image
                    LandmarkImage.objects.create(
                        landmark=landmark_instance,
                        # Saving the relative path for easy access
                        image=f"data/raw/{landmark_name_sanitized}/{new_filename}",
                        source='UPLOAD',
                        user=request.user if request.user.is_authenticated else None
                    )

                    uploaded_count += 1
                    next_image_idx += 1 
                except Exception as e:
                    return Response({'error': f'Failed to upload {file_obj.name}: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if uploaded_count == 0:
            return Response({'error': 'No files uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': f'Successfully uploaded {uploaded_count} images for {landmark_name}.', 
            'uploaded_count': uploaded_count
        }, status=status.HTTP_200_OK)


class TrainModelView(APIView):
    def post(self, request):
        landmark_name = request.data.get('landmark_name')
        
        # 1. Create the run log entry first
        run_log = TrainingRun.objects.create(
            model_name=f"{landmark_name}",
            epochs=5,
            status='processing'
        )

        try:
            # 2. Start the training process
            results = train_model(landmark_name)

            if results.get('status') == 'Complete':
                # 3. Explicitly save stats to the database
                run_log.accuracy = results.get('final_accuracy')
                run_log.loss = results.get('final_loss')
                run_log.image_count = results.get('total_images_processed')
                run_log.status = 'success'
                run_log.finished_at = timezone.now()
                run_log.save()
                
                return Response(results, status=status.HTTP_200_OK)
            else:
                run_log.status = 'failed'
                run_log.save()
                return Response({'error': results.get('message')}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            run_log.status = 'failed'
            run_log.save()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TrainingHistoryView(APIView):
    def get(self, request):
        # Returns the 5 most recent training runs
        runs = TrainingRun.objects.all().order_by('-started_at')[:5]
        serializer = TrainingRunSerializer(runs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class LandmarkPredictionView(APIView):
    def post(self, request):
        image_file = request.FILES.get('file')
        if not image_file: return Response({'error': 'No image'}, status=400)

        try:
            prediction = predict_image(image_file.read())
            name = prediction['label']
            landmark = Landmark.objects.get(name=name)
            
            if not landmark.summary:
                facts = get_landmark_facts(name)
                landmark.summary = generate_summary(name, facts)
                landmark.save()

            # Save the "Prediction Report"
            # This stores the history for the user
            LandmarkPrediction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                predicted_landmark=landmark,
                confidence=prediction['confidence'],
                summary_at_prediction=landmark.summary
            )

            return Response({
                'id': landmark.id,
                'name': landmark.name,
                'latitude': landmark.latitude,
                'longitude': landmark.longitude,
                'summary': landmark.summary,
                'confidence': prediction['confidence']
            }, status=200)

        except Landmark.DoesNotExist:
            return Response({'error': 'Landmark not in database'}, status=404)

class LandmarkListView(APIView):
    def get(self, request, *args, **kwargs):
        landmarks = Landmark.objects.all()
        serializer = LandmarkSerializer(landmarks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK) 

class ScrapeLandmarkView(APIView):
    def post(self, request, *args, **kwargs):
        landmark_name = request.data.get('landmark_name')
        search_query = request.data.get('search_query', None)

        if not landmark_name:
            return Response({'error': 'Landmark name is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        landmark_instance = get_or_create_landmark(landmark_name)
        if not landmark_instance:
            return Response({'error': f'Could not find or create landmark "{landmark_name}".'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # The service now returns the list of filenames as intended
            scraped_filenames = scrape_images_for_landmark(landmark_instance.name, search_query)
            
            # Use bulk_create for much faster database insertion
            image_objects = [
                LandmarkImage(
                    landmark=landmark_instance,
                    image=f"data/raw/{landmark_instance.name}/{fname}",
                    source='SCRAPED',
                    user=request.user if request.user.is_authenticated else None
                ) for fname in scraped_filenames
            ]
            
            with transaction.atomic():
                LandmarkImage.objects.bulk_create(image_objects)

            return Response({
                'message': f'Scraped {len(scraped_filenames)} images for {landmark_name}.', 
                'scraped_count': len(scraped_filenames)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DistanceCalculatorView(APIView):
    def post(self, request):
        landmark_name = request.data.get('landmark_name')
        origin_city = request.data.get('origin_city')

        if not landmark_name or not origin_city:
            return Response({"error": "Missing data"}, status=400)

        try:
            formatted_name = landmark_name.lower().replace(" ", "_") 
            landmark = Landmark.objects.get(name=formatted_name)
            metrics = distance_to_landmark(landmark, origin_city=origin_city)
            
            return Response({
                "distance_km": metrics["distance_km"],
                "estimated_cost": metrics["estimated_cost"]
            })
        except Landmark.DoesNotExist:
            return Response({'error': f"Landmark '{landmark_name}' not found in database."}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

# Configure your Gemini API Key here
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class LandmarkChatView(APIView):
    def post(self, request):
        user_query = request.data.get('message')
        history_data = request.data.get('history', [])
        
        if not user_query:
            return Response({"error": "Message is required"}, status=400)

        system_instruction = (
            "You are a specialized travel assistant for this Landmark App. "
            "1. Only answer questions about planning trips, landmarks, and travel features. "
            "2. If the user asks about politics, sports, coding, or random topics, politely say: "
            "'I'm specialized in landmark travel planning. Let's get back to your trip!'. "
            "3. Keep responses concise."
        )

        try:
            # 1. Format history for the Chat Session
            # Gemini expects 'user' and 'model'
            history_for_gemini = []
            # We skip the very first intro message and the last message (which is the current query)
            for msg in history_data[:-1]: 
                if msg['text'] == "Hi! I'm your Landmark Assistant. Ask me anything about your trip!":
                    continue
                role = "user" if msg['sender'] == 'user' else "model"
                history_for_gemini.append({"role": role, "parts": [{"text": msg['text']}]})

            # 2. Start a chat session with the history
            chat = client.chats.create(
                model="gemini-2.5-flash",
                config={
                    "system_instruction": system_instruction,
                },
                history=history_for_gemini
            )

            # 3. Send the current message
            response = chat.send_message(user_query)
            bot_answer = response.text.strip()

            # Store in DB
            ChatMessage.objects.create(
                user=request.user if request.user.is_authenticated else None,
                question=user_query,
                answer=bot_answer
            )

            return Response({"answer": bot_answer})

        except Exception as e:
            print(f"Gemini Error: {e}")
            return Response({"error": "I'm having trouble thinking right now."}, status=500)