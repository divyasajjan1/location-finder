from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Landmark, UserLocation, LandmarkPrediction
from .serializers import LandmarkSerializer, UserLocationSerializer, LandmarkPredictionSerializer

from api.utils.user_location import get_user_location
from api.utils.distance_to_landmark import distance_to_landmark
from api.utils.landmark_facts import get_landmark_facts
from api.utils.gemini_summary import generate_summary
from .predict import predict_image # Import from the new predict.py


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
            try:
                predicted_landmark_instance = Landmark.objects.get(name=predicted_landmark_name)
            except Landmark.DoesNotExist:
                return Response({'error': f'Predicted landmark "{predicted_landmark_name}" not found in database. Please populate initial landmark data.'}, status=status.HTTP_404_NOT_FOUND)

            # 3. Calculate distance
            distance_km = distance_to_landmark(predicted_landmark_name)

            # 4. Get landmark facts and summary
            facts = get_landmark_facts(predicted_landmark_name)
            summary = None
            if facts:
                summary = generate_summary(predicted_landmark_name, facts)
            
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
