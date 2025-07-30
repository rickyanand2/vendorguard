# common/models.py

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created_by",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated_by",
    )

    class Meta:
        abstract = True


#### Taxonomy Models ######
class DataType(models.Model):
    code = models.CharField(max_length=20, unique=True)
    label = models.CharField(max_length=255)
    risk_score = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Data Type"
        verbose_name_plural = "Data Types"
        ordering = ["label"]

    def __str__(self):
        return self.label
