from django.contrib import auth
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError

from rest_framework import serializers
from rest_framework import relations

from .models import Content, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag

    def to_native(self, obj):
        return {
            'id': obj.pk,
            'name': obj.name,
            'slug': obj.slug,
            'type': obj.get_mapping_type_name()
        }


class TagField(relations.RelatedField):
    """This is a relational field that handles the addition of tags to content
    objects. This field also allows the user to create tags in the db if they
    don't already exist."""

    read_only = False

    def to_native(self, obj):
        return {
            'id': obj.pk,
            'name': obj.name,
            'slug': obj.slug,
            'type': obj.get_mapping_type_name()
        }

    def from_native(self, value):
        """Basically, each tag dict must include a full dict with id,
        name and slug--or else you need to pass in a dict with just a name,
        which indicated that the Tag doesn't exist, and should be added."""

        if 'id' in value:
            tag = Tag.objects.get(id=value['id'])
        else:
            if 'name' not in value:
                raise ValidationError("Tags must include an ID or a name.")
            name = value['name']
            slug = value.get('slug', slugify(name))
            try:
                # Make sure that a tag with that slug doesn't already exist.
                tag = Tag.objects.get(slug=slug)
            except Tag.DoesNotExist:
                tag = Tag.objects.create(name=name, slug=slug)
        return tag


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth.get_user_model()
        exclude = ('password',)


class AuthorField(relations.RelatedField):
    """This field manages the authors on a piece of content, and allows a "fatter"
    endpoint then would normally be possible with a RelatedField"""

    read_only = False

    def to_native(self, obj):
        return {
            'id': obj.pk,
            'first_name': obj.first_name,
            'last_name': obj.last_name,
            'username': obj.username
        }

    def from_native(self, value):
        """Basically, each author dict must include either a username or id."""
        model = auth.get_user_model()

        if 'id' in value:
            author = model.objects.get(id=value['id'])
        else:
            if 'username' not in value:
                raise ValidationError("Authors must include an ID or a username.")
            username = value['username']
            author = model.objects.get(username=username)
        return author


class ContentSerializer(serializers.ModelSerializer):
    tags = TagField(many=True)
    authors = AuthorField(many=True)

    class Meta:
        model = Content


class PolymorphicContentSerializerMixin(object):
    def to_native(self, value):
        if value:
            if hasattr(value, 'get_serializer_class'):
                ThisSerializer = value.get_serializer_class()
            else:
                class ThisSerializer(serializers.ModelSerializer):
                    class Meta:
                        model = value.__class__
            
            serializer = ThisSerializer(context=self.context)
            return serializer.to_native(value)
        else:
            return super(PolymorphicContentSerializerMixin, self).to_native(value)


class PolymorphicContentSerializer(PolymorphicContentSerializerMixin, ContentSerializer):
    pass

