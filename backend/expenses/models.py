from django.db import models
from colorfield.fields import ColorField
import uuid

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=200)
    order = models.IntegerField()
    color = ColorField(default='#FF0000')
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.name} - {self.order}"


class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    amount = models.FloatField()
    source = models.CharField(max_length=200)
    spent_at = models.DateTimeField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)  # TODO should be set to some "other" category
    notes = models.CharField(max_length=1000, blank=True, null=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"${self.amount} at {self.source} on {self.spent_at} ({self.category})"
