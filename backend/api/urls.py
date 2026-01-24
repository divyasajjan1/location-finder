from django.urls import path
from .views import LandmarkPredictionView, LandmarkListView, ScrapeLandmarkView

urlpatterns = [
    path('predict/', LandmarkPredictionView.as_view(), name='predict_landmark'),
    path('landmarks/', LandmarkListView.as_view(), name='landmark_list'),
    path('scrape/', ScrapeLandmarkView.as_view(), name='scrape_landmark'), # New URL for scraping
]
