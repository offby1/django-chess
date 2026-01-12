from django.urls import path, include
from rest_framework.routers import DefaultRouter

from django_chess.api.views import GameViewSet

# Create a router and register our viewset
router = DefaultRouter()
router.register(r'games', GameViewSet, basename='api-game')

urlpatterns = [
    path('', include(router.urls)),
]
