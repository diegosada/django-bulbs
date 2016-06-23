from djbetty.serializers import ImageFieldSerializer
from rest_framework import serializers

from .fields import RichTextField


class CopySerializer(serializers.Serializer):
    copy = RichTextField(required=True, field_size="long")


class ItemSerializer(CopySerializer):
    title = RichTextField(field_size="short")
    image = ImageFieldSerializer(required=False)


class XYItemSerializer(serializers.Serializer):
    title = RichTextField(field_size="short")
    copy_x = RichTextField(field_size="long")
    copy_y = RichTextField(field_size="long")


class ComparisonKeySerializer(serializers.Serializer):
    title = RichTextField(field_size="short")
    color = serializers.CharField()
    initial = serializers.CharField()


class ComparisonSerializer(serializers.Serializer):
    key_x = ComparisonKeySerializer()
    key_y = ComparisonKeySerializer()
    items = XYItemSerializer(many=True)


class ListInfographicDataSerializer(serializers.Serializer):
    is_numbered = serializers.BooleanField(default=False)
    items = ItemSerializer(many=True, required=False)


class ProConSerializer(serializers.Serializer):
    body = RichTextField(required=True, field_size="long")
    pro = CopySerializer(many=True)
    con = CopySerializer(many=True)


class StrongSideWeakSideSerializer(serializers.Serializer):
    body = RichTextField(required=True, field_size="long")
    strong = CopySerializer(many=True)
    weak = CopySerializer(many=True)


class TimelineSerializer(serializers.Serializer):
    items = ItemSerializer(many=True, required=False)
