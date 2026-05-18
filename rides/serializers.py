from rest_framework import serializers

from .models import Ride, RideEvent, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id_user", "role", "first_name", "last_name", "email", "phone_number"]


class RideEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideEvent
        fields = ["id_ride_event", "id_ride", "description", "created_at"]
        read_only_fields = ["created_at"]


class RideSerializer(serializers.ModelSerializer):
    rider_details = UserSerializer(source="id_rider", read_only=True)
    driver_details = UserSerializer(source="id_driver", read_only=True)
    todays_ride_events = RideEventSerializer(many=True, read_only=True)

    class Meta:
        model = Ride
        fields = [
            "id_ride",
            "status",
            "id_rider",
            "id_driver",
            "rider_details",
            "driver_details",
            "pickup_latitude",
            "pickup_longitude",
            "dropoff_latitude",
            "dropoff_longitude",
            "pickup_time",
            "todays_ride_events",
        ]

    def validate(self, data):
        if data.get("id_rider") == data.get("id_driver") and data.get("id_driver") is not None:
            raise serializers.ValidationError("The rider and driver cannot be the same")
        return data
