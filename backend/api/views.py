from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ml.inference.predict import predict_image

from api.utils.user_location import get_user_location
from api.utils.distance_to_landmark import distance_to_landmark

@csrf_exempt
def predict_landmark(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST an image file"}, status=400)

    if "file" not in request.FILES:
        return JsonResponse({"error": "No image file provided"}, status=400)

    try:
        image_file = request.FILES["file"]
        result = predict_image(image_file.read())

        predicted_landmark = result["label"]
        confidence = result["confidence"]

        user_lat, user_lon = get_user_location()
        distance_km = distance_to_landmark(predicted_landmark)

        return JsonResponse({
            "predicted_landmark": predicted_landmark,
            "confidence": confidence,
            "user_location": {"lat": user_lat, "lon": user_lon},
            "distance_km": round(distance_km, 2)
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
