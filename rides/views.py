from datetime import timedelta

from django.db import connection
from django.db.models import ExpressionWrapper, F, FloatField, Prefetch
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter

from .filters import RideFilter
from .models import Ride, RideEvent, User
from .pagination import RidePagination
from .serializers import RideEventSerializer, RideSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class RideViewSet(viewsets.ModelViewSet):
    serializer_class = RideSerializer
    pagination_class = RidePagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = RideFilter

    def get_queryset(self):
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        recent_events_prefetch = Prefetch(
            "rideevent_set",
            queryset=RideEvent.objects.filter(created_at__gte=twenty_four_hours_ago),
            to_attr="todays_ride_events",
        )

        queryset = Ride.objects.select_related("id_rider", "id_driver").prefetch_related(recent_events_prefetch).all()

        ref_lat = self.request.query_params.get("ref_lat", None)
        ref_lng = self.request.query_params.get("ref_lng", None)

        if ref_lat and ref_lng:
            try:
                ref_lat = float(ref_lat)
                ref_lng = float(ref_lng)

                box_radius = 0.1  # Start at roughly 10km
                local_count = queryset.filter(
                    pickup_latitude__range=((ref_lat - box_radius), (ref_lat + box_radius)),
                    pickup_longitude__range=((ref_lng - box_radius), (ref_lng + box_radius)),
                ).count()

                if local_count < 5:
                    box_radius = 0.25  # if less than 5 results, expand to about 25km

                queryset = queryset.filter(
                    pickup_latitude__range=((ref_lat - box_radius), (ref_lat + box_radius)),
                    pickup_longitude__range=((ref_lng - box_radius), (ref_lng + box_radius)),
                )

                # Math, distance^2 = (lat1-lat2)^2 + (lng1-lng2)^2
                queryset = queryset.annotate(
                    distance=ExpressionWrapper(
                        (F("pickup_latitude") - ref_lat) ** 2 + (F("pickup_longitude") - ref_lng) ** 2,
                        output_field=FloatField(),
                    )
                )
                return queryset.order_by("distance")

            except ValueError:
                # Handle malformed coordinates, skip distance annotation
                pass

        return queryset.order_by("-pickup_time")

    def dispatch(self, request, *args, **kwargs):
        connection.queries_log.clear()
        response = super().dispatch(request, *args, **kwargs)
        for index, query in enumerate(connection.queries, start=1):
            sql_cleaned = " ".join(query["sql"].split())
            print(f"SQL: {sql_cleaned}")
        print(f"Total queries: {len(connection.queries)}")
        return response


class RideEventViewSet(viewsets.ModelViewSet):
    queryset = RideEvent.objects.all()
    serializer_class = RideEventSerializer
