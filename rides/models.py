from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("rider", "Rider"),
        ("driver", "Driver"),
    )
    id_user = models.AutoField(primary_key=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="rider")
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"


class Ride(models.Model):
    STATUS_CHOICES = (
        ("en-route", "En-route"),
        ("pickup", "Pickup"),
        ("dropoff", "Dropoff"),
    )
    id_ride = models.AutoField(primary_key=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="en-route", db_index=True)
    id_rider = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="rides_as_rider")
    id_driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="rides_as_driver")
    pickup_latitude = models.FloatField(db_index=True)  # Indexing these for performance on sorting
    pickup_longitude = models.FloatField(db_index=True)
    dropoff_latitude = models.FloatField()
    dropoff_longitude = models.FloatField()
    pickup_time = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["pickup_latitude", "pickup_longitude"], name="idx_pickup_coords"),
        ]

    def __str__(self):
        return f"Ride {self.id_ride} - {self.status}"


class RideEvent(models.Model):
    id_ride_event = models.AutoField(primary_key=True)
    id_ride = models.ForeignKey(Ride, on_delete=models.SET_NULL, null=True)
    description = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"Ride Event {self.id_ride_event} - {self.description}"
