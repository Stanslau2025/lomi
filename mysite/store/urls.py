from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AgentViewSet,
    AuthViewSet,
    ProductViewSet,
    PromotionViewSet,
    ShopSettingsViewSet,
    UserBagViewSet,
    activate,
)

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("agents", AgentViewSet, basename="agent")
router.register("promotions", PromotionViewSet, basename="promotion")
router.register("bag", UserBagViewSet, basename="bag")
router.register("auth", AuthViewSet, basename="auth")

urlpatterns = [
    path("", include(router.urls)),
    path("activate/<uidb64>/<token>/", activate, name="activate"),
    path(
        "settings/",
        ShopSettingsViewSet.as_view({"get": "list", "patch": "update_settings"}),
        name="settings",
    ),
]
