from collections import OrderedDict

from django.utils.encoding import force_text

from rest_framework import serializers
from rest_framework.metadata import SimpleMetadata
from rest_framework.utils.field_mapping import ClassLookupDict

from djbetty.serializers import ImageFieldSerializer

from bulbs.content.serializers import AuthorField
from .data_serializers import (
    ComparisonKeySerializer, CopySerializer, EntrySerializer, XYEntrySerializer
)
from .fields import ColorField, RichTextField
from .serializers import InfographicSerializer, InfographicDataField


METADATA_ATTRIBUTES = [
    "field_size", "read_only", "label", "help_text", "min_length", "max_length",
    "min_value", "max_value", "child_label"
]


class InfographicMetadata(SimpleMetadata):

    @property
    def label_lookup(self):
        mapping = SimpleMetadata.label_lookup.mapping
        mapping.update({
            AuthorField: "string",
            ColorField: "color",
            ComparisonKeySerializer: "object",
            CopySerializer: "array",
            EntrySerializer: "array",
            XYEntrySerializer: "array",
            ImageFieldSerializer: "image",
            RichTextField: "richtext"
        })
        return ClassLookupDict(mapping)

    def determine_metadata(self, request, view):
        serializer_class = view.get_serializer_class()
        if issubclass(serializer_class, InfographicSerializer):
            data = self.get_custom_metadata(serializer_class, view)
            return data
        return super(InfographicMetadata, self).determine_metadata(request, view)

    def get_label_lookup(self, field):
        field_type = self.label_lookup[field]
        if field_type == "field" and hasattr(field, "child_relation"):
            return self.get_label_lookup(field.child_relation)
        return field_type

    def get_attributes(self, obj):
        info = dict()
        for attr in sorted(METADATA_ATTRIBUTES):
            value = getattr(obj, attr, None)
            if value is not None and value != "":
                info[attr] = force_text(value, strings_only=True)
        return info

    def get_field_info(self, field):
        """
        This method is basically a mirror from rest_framework==3.3.3

        We are currently pinned to rest_framework==3.1.1. If we upgrade,
        this can be refactored and simplified to rely more heavily on
        rest_framework's built in logic.
        """

        field_info = self.get_attributes(field)
        field_info["required"] = getattr(field, "required", False)
        field_info["type"] = self.get_label_lookup(field)

        if getattr(field, "child", None):
            field_info["child"] = self.get_field_info(field.child)
        elif getattr(field, "fields", None):
            field_info["children"] = self.get_serializer_info(field)

        if (not isinstance(field, (serializers.RelatedField, serializers.ManyRelatedField)) and
                hasattr(field, "choices")):
            field_info["choices"] = [
                {
                    "value": choice_value,
                    "display_name": force_text(choice_name, strings_only=True)
                }
                for choice_value, choice_name in field.choices.items()
            ]

        return field_info

    def get_serializer_info(self, serializer):
        serializer_info = super(InfographicMetadata, self).get_serializer_info(serializer)
        custom_params = OrderedDict()

        if hasattr(serializer, "child"):
            label = self.label_lookup[serializer.child]
            if hasattr(serializer.child, "child_label"):
                custom_params["child_label"] = serializer.child.child_label
        else:
            label = self.label_lookup[serializer]

        if label != "field":
            serializer_info = OrderedDict([
                ("type", label),
                ("fields", serializer_info)
            ])
            for key, value in custom_params.items():
                serializer_info[key] = value

        return serializer_info

    def get_custom_metadata(self, serializer, view):
        fields_metadata = dict()
        if hasattr(serializer, "__call__"):
            serializer_instance = serializer()
        else:
            serializer_instance = serializer
        for field_name, field in serializer_instance.get_fields().items():
            if isinstance(field, InfographicDataField):
                if view.suffix != "List":
                    serializer = view.get_object().get_data_serializer()
                    fields_metadata[field_name] = self.get_custom_metadata(serializer, view)
            elif isinstance(field, serializers.BaseSerializer):
                fields_metadata[field_name] = self.get_serializer_info(field)
            else:
                fields_metadata[field_name] = self.get_field_info(field)
        return {
            "fields": fields_metadata
        }
