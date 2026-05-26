from django.db import models
from django.conf import settings
from candidates.models import Candidate

class Cart(models.Model):
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart_items',
        limit_choices_to={'role': 'client'}
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='cart_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['client', 'candidate'], name='unique_client_candidate_cart')
        ]

    def __str__(self):
        return f"{self.client.full_name} -> {self.candidate.full_name}"
