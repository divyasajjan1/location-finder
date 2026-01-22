from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from scripts.training.predict import predict_image

from api.utils.user_location import get_user_location
from api.utils.distance_to_landmark import distance_to_landmark
from api.utils.landmark_facts import get_landmark_facts
from api.utils.gemini_summary import generate_summary


@csrf_exempt
def predict_landmark(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST an image file"}, status=400)

    files = request.FILES.getlist("file")

    if not files:
        return JsonResponse({"error": "No image file provided"}, status=400)

    results = []

    try:
        # Get user location once (not per image)
        user_lat, user_lon = get_user_location()

        for image_file in files:
            prediction = predict_image(image_file.read())

            predicted_landmark = prediction["label"]
            confidence = prediction["confidence"]

            distance_km = distance_to_landmark(predicted_landmark)

            facts = get_landmark_facts(predicted_landmark)
            summary = None
            if facts:
                summary = generate_summary(predicted_landmark, facts)

            results.append({
                "filename": image_file.name,
                "predicted_landmark": predicted_landmark,
                "confidence": confidence,
                "distance_km": round(distance_km, 2),
                "summary": summary
            })
        
        return JsonResponse({
            "user_location": {"lat": user_lat, "lon": user_lon},
            "results": results
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
