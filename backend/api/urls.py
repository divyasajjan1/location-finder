from django.urls import path
from .views import LandmarkPredictionView, LandmarkListView, RecalculateTravelView, ScrapeLandmarkView, BulkImageUploadView, TrainModelView

urlpatterns = [
    path('predict/', LandmarkPredictionView.as_view(), name='predict_landmark'),
    path('landmarks/', LandmarkListView.as_view(), name='landmark_list'),
    path('scrape/', ScrapeLandmarkView.as_view(), name='scrape_landmark'), # New URL for scraping
    path('bulk-upload/', BulkImageUploadView.as_view(), name='bulk_image_upload'),
    path('train/', TrainModelView.as_view(), name='train_model'),
    path('recalculate/', RecalculateTravelView.as_view(), name='recalculate_travel'),
]
