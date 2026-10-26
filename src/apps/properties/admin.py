"""Admin registrations used by the operations team."""

from django.contrib import admin

from apps.properties.models import ImportRun, Property, PropertyPhoto


class PropertyPhotoInline(admin.TabularInline):
    """Photos of the listing, in the order the portal displays them."""

    model = PropertyPhoto
    extra = 0


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """Catalog browsing for the operations team."""

    inlines = [PropertyPhotoInline]

    list_display = ("external_id", "source", "title", "city", "transaction", "price", "is_active")
    list_filter = ("source", "transaction", "is_active", "city")
    search_fields = ("external_id", "title", "address")


@admin.register(ImportRun)
class ImportRunAdmin(admin.ModelAdmin):
    """History of the portal imports and how each one went."""

    list_display = (
        "source",
        "status",
        "started_at",
        "finished_at",
        "created_count",
        "updated_count",
    )
    list_filter = ("source", "status")
