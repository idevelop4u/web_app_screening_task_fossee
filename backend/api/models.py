from django.db import models


class EquipmentDataset(models.Model):
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    analysis_results = models.JSONField() # Stores total_count, averages, etc.

    class Meta:
        ordering = ['-uploaded_at']

