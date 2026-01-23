from rest_framework import serializers
from .models import Landmark, UserLocation, LandmarkPrediction

class LandmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Landmark
        fields = '__all__'

class UserLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocation
        fields = '__all__'

class LandmarkPredictionSerializer(serializers.ModelSerializer):
    user_location = UserLocationSerializer(read_only=True)
    predicted_landmark = LandmarkSerializer(read_only=True)

    class Meta:
        model = LandmarkPrediction
        fields = '__all__'

