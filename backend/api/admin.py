from django.contrib import admin
from .models import Landmark, UserLocation, LandmarkPrediction

@admin.register(Landmark)
class LandmarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'summary', 'wikidata_id')

@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ('latitude', 'longitude', 'timestamp')

@admin.register(LandmarkPrediction)
class LandmarkPredictionAdmin(admin.ModelAdmin):
    list_display = ('user_location', 'predicted_landmark', 'confidence', 'distance_km', 'summary', 'prediction_timestamp')