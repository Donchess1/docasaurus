from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets

from console.models import Event
from console.serializers.event import EventSerializer
from utils.response import Response


class EventViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = EventSerializer
    http_method_names = ["get", "post", "put", "delete"]

    def list(self, request):
        events = Event.objects.all()
        serializer = self.serializer_class(events, many=True)
        return Response(
            success=True,
            message="Events retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

    def create(self, request):
        return self._save_event(request)

    def retrieve(self, request, pk=None):
        event = get_object_or_404(Event, id=pk)
        serializer = self.serializer_class(event)
        return Response(
            success=True,
            message="Event retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

    def update(self, request, pk=None):
        event = get_object_or_404(Event, id=pk)
        return self._save_event(request, instance=event)

    def destroy(self, request, pk=None):
        event = get_object_or_404(Event, id=pk)
        event.delete()
        return Response(
            success=True,
            message="Event deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    def _save_event(self, request, instance=None):
        serializer = self.serializer_class(
            instance, data=request.data, partial=bool(instance)
        )
        if serializer.is_valid():
            event = serializer.save()
            return Response(
                success=True,
                message="Event created successfully"
                if not instance
                else "Event updated successfully",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
                if not instance
                else status.HTTP_200_OK,
            )
        return Response(
            success=False,
            status_code=status.HTTP_400_BAD_REQUEST,
            errors=serializer.errors,
        )
