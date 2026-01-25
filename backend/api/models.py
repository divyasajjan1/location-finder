from django.db import models

class Landmark(models.Model):
    name = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    summary = models.TextField(null=True, blank=True)
    wikidata_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

class UserLocation(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"({self.latitude}, {self.longitude}) at {self.timestamp}"

class LandmarkPrediction(models.Model):
    user_location = models.ForeignKey(UserLocation, on_delete=models.CASCADE)
    predicted_landmark = models.ForeignKey(Landmark, on_delete=models.CASCADE)
    distance_km = models.FloatField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    prediction_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_location} predicted {self.predicted_landmark.name}"
