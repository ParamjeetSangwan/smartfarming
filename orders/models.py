# orders/models.py

from django.db import models
from django.contrib.auth.models import User
from marketplace.models import Tool, Pesticide

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_orders')
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    tool = models.ForeignKey('marketplace.Tool', on_delete=models.CASCADE, null=True, blank=True)
    pesticide = models.ForeignKey('marketplace.Pesticide', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
