from django.urls import path
from .views import LandmarkPredictionView, LandmarkListView

urlpatterns = [
    path('predict/', LandmarkPredictionView.as_view(), name='predict_landmark'),
    path('landmarks/', LandmarkListView.as_view(), name='landmark_list'),
]
