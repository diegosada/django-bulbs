from rest_framework import serializers

from bulbs.content.serializers import ContentSerializer
from bulbs.super_features.models import BaseSuperFeature
from bulbs.super_features.utils import get_data_serializer


class BaseSuperFeatureDataField(serializers.Field):

    def to_internal_value(self, data):
        serializer = get_data_serializer(
            self.parent.initial_data.get("superfeature_type")
        )
        return serializer().to_internal_value(data)

    def to_representation(self, obj):
        serializer_class = get_data_serializer(
            self.parent.initial_data.get("superfeature_type")
        )
        serializer = serializer_class(data=obj)
        serializer.is_valid(raise_exception=True)
        return serializer.data


class BaseSuperFeatureSerializer(ContentSerializer):

    data = BaseSuperFeatureDataField(required=False)

    class Meta:
        model = BaseSuperFeature
