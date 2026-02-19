from django.db import models
from django.contrib.auth.models import User

# 1. LANDMARKS (The core "Library")
class Landmark(models.Model):
    name = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    summary = models.TextField(null=True, blank=True)
    wikidata_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

# 2. IMAGES (Track source: Scraped vs Uploaded)
class LandmarkImage(models.Model):
    SOURCE_CHOICES = [('UPLOAD', 'Upload'), ('SCRAPED', 'Scraped')]
    
    landmark = models.ForeignKey(Landmark, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='landmark_images/') # Actual file storage
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# 3. PREDICTIONS (The "Report" history)
class LandmarkPrediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    predicted_landmark = models.ForeignKey(Landmark, on_delete=models.CASCADE)
    confidence = models.FloatField(null=True, blank=True)
    # Storing the summary at the time of prediction ensures history stays even if Landmark changes
    summary_at_prediction = models.TextField(null=True, blank=True) 
    prediction_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prediction: {self.predicted_landmark.name} ({self.confidence}%)"

# 4. TRAINING LOGS (Admin only feature)
class TrainingRun(models.Model):
    model_name = models.CharField(max_length=100)
    image_count = models.IntegerField(null=True, blank=True)
    epochs = models.IntegerField()
    accuracy = models.FloatField(null=True, blank=True)
    loss = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, default='processing') # processing, success, failed
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

# 5. CHAT (AI Interaction history)
class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    question = models.TextField()
    answer = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)