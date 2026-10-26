"""Endpoints and filters for the public catalog API."""

from django_filters.rest_framework import FilterSet, NumberFilter
from rest_framework import viewsets

from apps.properties.api.serializers import PropertySerializer
from apps.properties.models import Property


class PropertyFilter(FilterSet):
    """Search filters accepted by the catalog endpoint."""

    min_price = NumberFilter(field_name="price", lookup_expr="gte")
    max_price = NumberFilter(field_name="price", lookup_expr="lte")
    min_bedrooms = NumberFilter(field_name="bedrooms", lookup_expr="gte")

    class Meta:
        model = Property
        fields = ["city", "transaction", "min_price", "max_price", "min_bedrooms"]


class PropertyViewSet(viewsets.ReadOnlyModelViewSet[Property]):
    """Read-only catalog of the listings currently on offer.

    Listings withdrawn by their portal are kept in the database but never
    reach this endpoint.
    """

    serializer_class = PropertySerializer
    filterset_class = PropertyFilter
    queryset = Property.objects.filter(is_active=True)
