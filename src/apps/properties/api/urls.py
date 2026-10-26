"""Routes exposed by the catalog API."""

from rest_framework.routers import DefaultRouter

from apps.properties.api.views import PropertyViewSet

router = DefaultRouter()
router.register("properties", PropertyViewSet, basename="property")

urlpatterns = router.urls
