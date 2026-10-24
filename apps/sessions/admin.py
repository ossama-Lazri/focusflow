from django.contrib import admin
from .models import FocusSession


@admin.register(FocusSession)
class FocusSessionAdmin(admin.ModelAdmin):
    list_display = (
        "label",
        "status",
        "started_at",
        "stopped_at",
        "duration_formatted",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("label",)
    readonly_fields = ("created_at", "updated_at", "duration_formatted")
    ordering = ("-created_at",)
