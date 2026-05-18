from django.db.models import ExpressionWrapper, F, FloatField
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
        queryset = Ride.objects.prefetch_related("rideevent_set").all()

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


class RideEventViewSet(viewsets.ModelViewSet):
    queryset = RideEvent.objects.all()
    serializer_class = RideEventSerializer
