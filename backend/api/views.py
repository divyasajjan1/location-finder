from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Landmark, UserLocation, LandmarkPrediction
from .serializers import LandmarkSerializer, UserLocationSerializer, LandmarkPredictionSerializer

from api.utils.user_location import get_user_location
from api.utils.distance_to_landmark import distance_to_landmark
from api.utils.landmark_facts import get_landmark_facts
from api.utils.gemini_summary import generate_summary
from .predict import predict_image
import os
from django.conf import settings
from .scraping_service import scrape_images_for_landmark # New import
from .landmark_management import get_or_create_landmark # New import


class BulkImageUploadView(APIView):
    def post(self, request, *args, **kwargs):
        landmark_name = request.data.get('landmark_name')
        if not landmark_name:
            return Response({'error': 'Landmark name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        landmark_name_sanitized = landmark_name.lower().replace(" ", "_")
        upload_dir = os.path.join(settings.BASE_DIR.parent, 'data', 'raw', landmark_name_sanitized)
        os.makedirs(upload_dir, exist_ok=True)

        uploaded_count = 0
        existing_files = os.listdir(upload_dir)
        # Find the highest existing number to determine the next available number
        # This handles cases where files might be named like '1.jpg', 'image_2.png', etc.
        # We'll look for numbers in the filename (before the extension)
        highest_num = 0
        for fname in existing_files:
            try:
                # Remove extension, then try to convert to int
                name_without_ext = os.path.splitext(fname)[0]
                if name_without_ext.isdigit(): # Ensure it's purely a number
                    highest_num = max(highest_num, int(name_without_ext))
            except ValueError:
                # Ignore files that are not simply numbered
                pass
        
        next_image_idx = highest_num + 1

        for key, file_obj in request.FILES.items():
            if key.startswith('file'): # Handle multiple files with keys like file[0], file[1] etc.
                try:
                    # Construct new filename with numbered convention
                    new_filename = f"{next_image_idx}.jpg"
                    file_path = os.path.join(upload_dir, new_filename)
                    
                    with open(file_path, 'wb+') as destination:
                        for chunk in file_obj.chunks():
                            destination.write(chunk)
                    uploaded_count += 1
                    next_image_idx += 1 # Increment for the next file
                except Exception as e:
                    return Response({'error': f'Failed to upload {file_obj.name}: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                except Exception as e:
                    return Response({'error': f'Failed to upload {file_obj.name}: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if uploaded_count == 0:
            return Response({'error': 'No files uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': f'Successfully uploaded {uploaded_count} images for {landmark_name}.', 'uploaded_count': uploaded_count}, status=status.HTTP_200_OK)



class LandmarkPredictionView(APIView):
    def post(self, request, *args, **kwargs):
        image_file = request.FILES.get('file')

        if not image_file:
            return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Get user location
            user_lat, user_lon = get_user_location()
            if user_lat is None or user_lon is None:
                return Response({'error': 'Could not determine user location'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            user_location_instance = UserLocation.objects.create(latitude=user_lat, longitude=user_lon)

            # 2. Predict landmark from image
            prediction = predict_image(image_file.read())
            predicted_landmark_name = prediction['label']
            confidence = prediction['confidence']

            # Ensure the predicted landmark exists in our database
            # First, try to get the landmark. If not found, use get_or_create_landmark
            predicted_landmark_instance = Landmark.objects.get(name=predicted_landmark_name)
            
            summary = predicted_landmark_instance.summary
            if not summary:
                # 4. Get landmark facts and summary
                facts = get_landmark_facts(predicted_landmark_name)
                if facts:
                    summary = generate_summary(predicted_landmark_name, facts)
                    predicted_landmark_instance.summary = summary
                    predicted_landmark_instance.save()
            
            # 3. Calculate distance
            distance_km = distance_to_landmark(predicted_landmark_name)
            
            # 5. Save prediction result
            landmark_prediction = LandmarkPrediction.objects.create(
                user_location=user_location_instance,
                predicted_landmark=predicted_landmark_instance,
                distance_km=distance_km,
                summary=summary
            )

            serializer = LandmarkPredictionSerializer(landmark_prediction)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LandmarkListView(APIView):
    def get(self, request, *args, **kwargs):
        landmarks = Landmark.objects.all()
        serializer = LandmarkSerializer(landmarks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ScrapeLandmarkView(APIView):
    def post(self, request, *args, **kwargs):
        landmark_name = request.data.get('landmark_name')
        search_query = request.data.get('search_query', None) # Repurposed from frontend's URL

        if not landmark_name:
            return Response({'error': 'Landmark name is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        landmark_instance = get_or_create_landmark(landmark_name)
        if not landmark_instance:
            return Response({'error': f'Could not find or create landmark "{landmark_name}". Please check the name or try again later.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            scraped_count = scrape_images_for_landmark(landmark_instance.name, search_query)
            return Response({'message': f'Scraped {scraped_count} images for {landmark_name}.', 'scraped_count': scraped_count}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
