"""Serializers for the public catalog API."""

from rest_framework import serializers

from apps.properties.models import Property


class PropertySerializer(serializers.ModelSerializer[Property]):
    """Public representation of a listing in the catalog.

    Source and transaction are rendered with their human readable labels rather
    than the codes we store.
    """

    source = serializers.CharField(source="get_source_display", read_only=True)
    transaction = serializers.CharField(source="get_transaction_display", read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "source",
            "external_id",
            "title",
            "description",
            "transaction",
            "price",
            "bedrooms",
            "bathrooms",
            "parking_spaces",
            "area_m2",
            "address",
            "neighborhood",
            "city",
            "state",
            "updated_at",
        ]
