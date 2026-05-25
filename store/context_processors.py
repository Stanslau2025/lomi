import json

from django.conf import settings


def lomi_store_context(request):
    user_json = None
    if request.user.is_authenticated:
        user_data = {
            "id": request.user.id,
            "email": request.user.email,
            "fullName": request.user.get_full_name() or request.user.username,
            "role": "admin" if request.user.is_staff else "customer",
        }
        if hasattr(request.user, "agent_profile"):
            user_data["role"] = "agent"
            user_data["agentId"] = str(request.user.agent_profile.id)
        user_json = json.dumps(user_data)

    return {
        "api_base_url": getattr(settings, "LOMI_API_BASE_URL", "/api"),
        "is_authenticated": request.user.is_authenticated,
        "user_json": user_json,
        "debug": settings.DEBUG,
        "environment": getattr(settings, "ENVIRONMENT", "development"),
        "cloudinary_cloud_name": getattr(settings, "CLOUDINARY_CLOUD_NAME", ""),
        "cloudinary_upload_preset": getattr(settings, "CLOUDINARY_UPLOAD_PRESET", ""),
    }
