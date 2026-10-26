"""Photos published by the portals for each listing."""

from django.db import models

from apps.properties.models.property import Property


class PropertyPhoto(models.Model):
    """A photo of a listing, in the order the portal publishes it."""

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="photos")
    url = models.URLField(max_length=500)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "property photo"
        verbose_name_plural = "property photos"
        ordering = ["position"]

    def __str__(self) -> str:
        """Return the listing the photo belongs to and its position."""
        return f"{self.property.external_id} #{self.position}"
