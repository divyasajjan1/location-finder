from django.urls import path
from .views import LandmarkPredictionView, DistanceCalculatorView, LandmarkListView, ScrapeLandmarkView, BulkImageUploadView, TrainModelView, TrainingHistoryView, LandmarkChatView

urlpatterns = [
    path('predict/', LandmarkPredictionView.as_view(), name='predict_landmark'),
    path('distance/', DistanceCalculatorView.as_view(), name='distance_calculator'),
    path('landmarks/', LandmarkListView.as_view(), name='landmark_list'),
    path('scrape/', ScrapeLandmarkView.as_view(), name='scrape_landmark'), 
    path('bulk-upload/', BulkImageUploadView.as_view(), name='bulk_image_upload'),
    path('train/', TrainModelView.as_view(), name='train_model'),
    path('training-history/', TrainingHistoryView.as_view(), name='training_history'),
    path('chat/', LandmarkChatView.as_view(), name='landmark_chat'),  
]
