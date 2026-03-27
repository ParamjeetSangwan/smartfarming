# orders/models.py

from django.db import models
from django.contrib.auth.models import User


class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True)
    address_line = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    landmark = models.CharField(max_length=200, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} — {self.city}, {self.state} {self.pincode}"

    def full_address(self):
        parts = [self.address_line]
        if self.landmark:
            parts.append(f"Near {self.landmark}")
        parts.append(f"{self.city}, {self.state} - {self.pincode}")
        return ", ".join(parts)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('processing', 'Processing'),
        ('shipped',    'Shipped'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
        ('returned',   'Returned'),
    ]

    PAYMENT_CHOICES = [
        ('cod',      'Cash on Delivery'),
        ('razorpay', 'Razorpay'),
        ('stripe',   'Stripe'),
        ('upi',      'UPI'),
        ('card',     'Credit / Debit Card'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    shipping_address = models.ForeignKey(
        ShippingAddress, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders'
    )
    total_price = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending','Pending'),('paid','Paid'),('failed','Failed'),('refunded','Refunded')],
        default='pending'
    )
    # UPI transaction ID entered by customer — admin verifies this manually
    upi_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} — {self.user.username} ({self.status})"

    @property
    def is_revenue(self):
        return self.status == 'delivered' and self.payment_status == 'paid'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    item_type = models.CharField(max_length=50, default='tool')
    item_id = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=100, default='unknown')
    price = models.FloatField(default=0)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity