from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from bulbs.api.permissions import CanEditContent
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    paginate_by = 20
    permission_classes = [IsAdminUser]


class ReadOnlyNotificationViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Notification.objects.filter(is_published=True)
    serializer_class = NotificationSerializer
    paginate_by = 20
