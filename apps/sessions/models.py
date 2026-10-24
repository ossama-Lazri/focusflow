from django.db import models
from django.utils import timezone


class FocusSession(models.Model):
    STATUS_IDLE = 'idle'
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    label = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IDLE)
    started_at = models.DateTimeField(null=True, blank=True)
    stopped_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Focus Session'
        verbose_name_plural = 'Focus Sessions'

    def __str__(self):
        return f"{self.label} ({self.status})"

    @property
    def duration_formatted(self):
        """Return a human-readable duration string."""
        h = self.duration_seconds // 3600
        m = (self.duration_seconds % 3600) // 60
        s = self.duration_seconds % 60
        if h:
            return f"{h}h {m}m {s}s"
        elif m:
            return f"{m}m {s}s"
        return f"{s}s"

    @property
    def elapsed_seconds(self):
        """Return the elapsed seconds for an active session."""
        if self.status == self.STATUS_ACTIVE and self.started_at:
            delta = timezone.now() - self.started_at
            return int(delta.total_seconds())
        return self.duration_seconds

    @property
    def elapsed_formatted(self):
        """Return human-readable elapsed time for active or completed sessions."""
        secs = self.elapsed_seconds
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
