from django.contrib import admin
# Removed UserLocation from the import list
from .models import (
    Landmark, 
    LandmarkPrediction, 
    LandmarkImage, 
    TrainingRun, 
    TripPlan, 
    ChatMessage
)

# Register your new models so you can see them in the Django Admin
admin.site.register(Landmark)
admin.site.register(LandmarkPrediction)
admin.site.register(LandmarkImage)
admin.site.register(TrainingRun)
admin.site.register(TripPlan)
admin.site.register(ChatMessage)