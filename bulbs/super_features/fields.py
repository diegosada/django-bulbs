from rest_framework import serializers

# TODO: Move to common file
class RichTextField(serializers.CharField):

    def __init__(self, *args, **kwargs):
        self.field_size = kwargs.pop("field_size", None)
        super(RichTextField, self).__init__(*args, **kwargs)
