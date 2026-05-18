import os
import random
from datetime import timedelta

import django
from django.contrib.auth import get_user_model
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from rides.models import Ride, RideEvent  # noqa: E402

User = get_user_model()


def seed_database():
    print("Cleaning existing data...")
    RideEvent.objects.all().delete()
    Ride.objects.all().delete()
    User.objects.filter(is_staff=False).delete()

    print("Creating Riders and Drivers...")
    riders = []
    drivers = []

    for i in range(1, 11):
        rider = User.objects.create_user(
            username=f"rider_{i}",
            email=f"rider{i}@example.com",
            password="password123",
            first_name="Rider",
            last_name=str(i),
            role="rider",
            phone_number=f"+161755501{i:02d}",
        )
        riders.append(rider)

        driver = User.objects.create_user(
            username=f"driver_{i}",
            email=f"driver{i}@example.com",
            password="password123",
            first_name="Driver",
            last_name=str(i),
            role="driver",
            phone_number=f"+161755502{i:02d}",
        )
        drivers.append(driver)

    print("Generating Rides centered around Boston...")
    boston_lat, boston_lng = 42.3557, -71.0656
    statuses = ["en-route", "pickup", "dropoff"]

    for i in range(50):
        p_lat = boston_lat + random.uniform(-0.04, 0.04)
        p_lng = boston_lng + random.uniform(-0.04, 0.04)
        d_lat = p_lat + random.uniform(-0.02, 0.02)
        d_lng = p_lng + random.uniform(-0.02, 0.02)

        status = random.choice(statuses)
        rider = random.choice(riders)
        driver = random.choice(drivers)

        ride_duration_days = random.choice([1, 2, 3])
        hours_per_step = {1: 12, 2: 18, 3: 24}[ride_duration_days]
        random_hours_ago = random.randint(72, 144)
        base_time = timezone.now() - timedelta(hours=random_hours_ago)

        ride = Ride.objects.create(
            status=status,
            id_rider=rider,
            id_driver=driver,
            pickup_latitude=p_lat,
            pickup_longitude=p_lng,
            dropoff_latitude=d_lat,
            dropoff_longitude=d_lng,
            pickup_time=base_time,
        )

        event_time = base_time
        event1 = RideEvent.objects.create(id_ride=ride, description="Ride requested.")
        event1.created_at = event_time
        event1.save()

        if status in ["pickup", "en-route", "dropoff"]:
            event_time += timedelta(hours=hours_per_step)
            event2 = RideEvent.objects.create(id_ride=ride, description="Driver matched.")
            event2.created_at = event_time
            event2.save()

        if status in ["en-route", "dropoff"]:
            event_time += timedelta(hours=hours_per_step)
            event3 = RideEvent.objects.create(id_ride=ride, description="Passenger picked up.")
            event3.created_at = event_time
            event3.save()

        if status == "dropoff":
            event_time += timedelta(hours=hours_per_step)
            event4 = RideEvent.objects.create(id_ride=ride, description="Ride completed.")
            event4.created_at = event_time
            event4.save()

    print(f"Seeding complete! Created 10 Riders, 10 Drivers, 50 Rides, and {RideEvent.objects.count()} simple events.")


if __name__ == "__main__":
    seed_database()
