from django.urls import path
from .views import predict_landmark

urlpatterns = [
    path("predict/", predict_landmark, name="predict_landmark"),
]
