from django.contrib import admin
from .models import UserProfile, OTPVerification, Notification, Announcement, AdminTwoFactor

# FIX: was completely empty — none of these were visible in /admin/
admin.site.register(UserProfile)
admin.site.register(OTPVerification)
admin.site.register(Notification)
admin.site.register(Announcement)
admin.site.register(AdminTwoFactor)