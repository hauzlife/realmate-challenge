"""The listing we expose in the catalog, normalised across every portal."""

from django.db import models


class Property(models.Model):
    """A real estate listing published by a partner portal.

    Every portal keeps its own identifier for a listing. The pair of `source`
    and `external_id` is how we recognise a listing we have imported before.
    """

    class Source(models.TextChoices):
        NEXO = "NEXO", "Nexo Portal"

    class Transaction(models.TextChoices):
        SALE = "SALE", "Sale"
        RENT = "RENT", "Rent"

    source = models.CharField(max_length=32, choices=Source.choices)
    external_id = models.CharField(max_length=64)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    transaction = models.CharField(max_length=8, choices=Transaction.choices)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    bedrooms = models.PositiveSmallIntegerField(default=0)
    bathrooms = models.PositiveSmallIntegerField(default=0)
    parking_spaces = models.PositiveSmallIntegerField(default=0)
    area_m2 = models.PositiveIntegerField(null=True, blank=True)

    address = models.CharField(max_length=255)
    neighborhood = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=2)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "property"
        verbose_name_plural = "properties"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["source", "external_id"], name="idx_property_source_ext"),
            models.Index(fields=["city", "transaction"], name="idx_property_city_trans"),
        ]

    def __str__(self) -> str:
        """Return a label identifying the listing and the portal it came from."""
        return f"{self.get_source_display()} #{self.external_id} - {self.title}"
