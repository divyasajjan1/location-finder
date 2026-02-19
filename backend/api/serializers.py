from rest_framework import serializers
from .models import Landmark, LandmarkPrediction, LandmarkImage, TrainingRun, ChatMessage

# 1. LANDMARK SERIALIZER
class LandmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Landmark
        fields = ['id', 'name', 'latitude', 'longitude', 'summary', 'wikidata_id']

# 2. PREDICTION SERIALIZER (Historical Report)
class LandmarkPredictionSerializer(serializers.ModelSerializer):
    # Nesting the landmark details so the frontend has the name/coords easily
    predicted_landmark = LandmarkSerializer(read_only=True)
    
    class Meta:
        model = LandmarkPrediction
        fields = [
            'id', 'user', 'predicted_landmark', 'confidence', 
            'distance_km', 'summary_at_prediction', 'prediction_timestamp'
        ]

# 3. TRAINING RUN SERIALIZER (For Admin Monitoring)
class TrainingRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingRun
        fields = [
            'id', 'model_name', 'image_count', 'epochs', 'accuracy', 
            'loss', 'status', 'started_at', 'finished_at'
        ]

# 5. CHAT MESSAGE SERIALIZER
class ChatMessageSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'username', 'question', 'answer', 'timestamp']

# 6. LANDMARK IMAGE SERIALIZER (Optional/Internal use)
class LandmarkImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandmarkImage
        fields = ['id', 'landmark', 'image', 'source', 'user', 'created_at']