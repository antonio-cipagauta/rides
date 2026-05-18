from django.urls import include, path
from rest_framework.routers import DefaultRouter

from rides.views import RideEventViewSet, RideViewSet, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"rides", RideViewSet, basename="ride")
router.register(r"events", RideEventViewSet, basename="event")

urlpatterns = [
    path("", include(router.urls)),
]
