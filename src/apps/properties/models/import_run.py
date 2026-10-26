"""Bookkeeping for portal imports."""

from django.db import models


class ImportRun(models.Model):
    """A single execution of a portal import.

    Answers "did the import run?", "how long did it take?" and "what came in?"
    without having to dig through the logs.
    """

    class Status(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Succeeded"
        FAILED = "FAILED", "Failed"

    source = models.CharField(max_length=32)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RUNNING)

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)

    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "import run"
        verbose_name_plural = "import runs"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        """Return the portal, the outcome and when the run started."""
        return f"{self.source} {self.status} ({self.started_at:%d/%m/%Y %H:%M})"
