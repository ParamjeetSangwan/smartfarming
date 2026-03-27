# government_schemes/models.py

from django.db import models
from django.contrib.auth.models import User


class SchemeInterest(models.Model):
    STATUS_CHOICES = [
        ('interested', 'Interested'),
        ('applied', 'Applied'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheme_interests')
    scheme_id = models.IntegerField()
    scheme_name = models.CharField(max_length=300)
    scheme_category = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='interested')
    clicked_apply = models.BooleanField(default=False)   # clicked "Apply / Learn More"
    self_marked_applied = models.BooleanField(default=False)  # clicked "I Applied"
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'scheme_id')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} → {self.scheme_name} [{self.status}]"