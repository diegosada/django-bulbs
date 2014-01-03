from django.conf import settings
from django.db import models

from elasticutils import S, MappingType, SearchResults
from elasticutils.contrib.django import get_es


class ModelSearchResults(SearchResults):
    """This is a little hackey, but in this class, "type" is a polymorphic classmethod
    that we're supposed to return results for."""

    def set_objects(self, results):
        ids = list(int(r['_id']) for r in results)
        model_objects = self.type.get_model().objects.in_bulk(ids)
        self.objects = [
            model_objects[id] for id in ids if id in model_objects
        ]

    def __iter__(self):
        return self.objects.__iter__()


class PolymorphicS(S):
    """A custom S class, adding a few methods to ease searching for Polymorphic objects"""

    def __init__(self, type_=None):
        """The base S class has "as_list" and "as_dict", and we need to add "as_models"."""
        super(PolymorphicS, self).__init__(type_=type_)
        self.as_models = False

    def _clone(self, next_step=None):
        """Since we have some special stuff in this S class, we need to pass it along when we clone."""
        new = super(PolymorphicS, self)._clone(next_step=next_step)
        new.as_models = self.as_models
        return new

    def get_doctypes(self):
        for action, value in reversed(self.steps):
            if action == 'doctypes':
                return list(value)
        return None

    def instanceof(self, klass, exact=False):
        """This gets results that are of this type, or inherit from it.

        If exact is True, only results for this exact class are returned. Otherwise, child objects
        are included in the response."""
        if exact:
            doctypes = [klass.get_mapping_type_name()]
        else:
            doctypes = klass.get_mapping_type_names()
        return self._clone(next_step=('doctypes', doctypes))

    def get_results_class(self):
        if self.as_models:
            return ModelSearchResults
        return super(PolymorphicS, self).get_results_class()

    def full(self):
        """This will allow the search to return full model instances, using ModelSearchResults"""
        self.as_models = True
        return self._clone(next_step=('values_list', ['_id']))

    def all(self):
        """
        Fixes the default `S.all` method given by elasticutils.
        `S` generally looks like django queryset but differs in
        a few ways, one of which is `all`. Django's `QuerySet.all()`
        returns a clone but `S` returns all the documents at once.
        This makes `all` at least respect slices but the real fix
        is to probably make `S` work more like `QuerySet`.
        """
        if self.start == 0 and self.stop is None:
            # no slicing has occurred. let's get all of the records.
            count = self.count()
            return self[:count].execute()
        return self.execute()


class PolymorphicMappingType(MappingType):

    @classmethod
    def get_model(cls):
        return cls.base_polymorphic_class

    @classmethod
    def get_index(cls):
        return cls.base_polymorphic_class.get_index_name()


class SearchManager(models.Manager):
    """This custom Manager provides some helper methods to easily query and filter elasticsearch
    results for polymorphic objects."""

    def s(self):
        """Returns a PolymorphicS() instance, using an ES URL from the settings, and an index
        from this manager's model"""

        base_polymorphic_class = self.model.get_base_class()
        type_ = type('%sMappingType' % base_polymorphic_class.__name__, (PolymorphicMappingType,), {'base_polymorphic_class': base_polymorphic_class})

        return PolymorphicS(type_=type_).es(urls=settings.ES_URLS)

    @property
    def es(self):
        """Returns a pyelasticsearch object, using the ES URL from the Django settings"""
        return get_es(urls=settings.ES_URLS)

    def refresh(self):
        """Refreshes the index for this object"""
        return self.es.refresh(index=self.model.get_index_name())

    def query(self, **kwargs):
        """Just a simple bridge to elasticutils' S().query(), prepopulating the URL
        and index information"""
        return self.s().query(**kwargs)

    def filter(self, **kwargs):
        """Just a simple bridge to elasticutils' S().filter(), prepopulating the URL
        and index information"""
        return self.s().filter(**kwargs)


class PolymorphicIndexable(object):
    """Base mixin for polymorphic indexin'"""

    search = SearchManager()

    def extract_document(self):
        # Regarding primary key field name of PolymorphicModel subclasses:
        # https://github.com/chrisglass/django_polymorphic/blob/master/polymorphic/query.py#L190
        return {
            'polymorphic_ctype': self.polymorphic_ctype_id,
            self.polymorphic_primary_key_name: self.id
        }

    @classmethod
    def get_base_class(cls):
        while cls.__bases__[0] != PolymorphicIndexable:
            cls = cls.__bases__[0]
        return cls

    @classmethod
    def get_index_name(cls):
        return cls.get_base_class()._meta.db_table

    @classmethod
    def get_es(cls):
        return get_es(urls=settings.ES_URLS).index(cls.get_index_name())

    @classmethod
    def get_mapping(cls):
        return {
            cls.get_mapping_type_name(): {
                '_id': {
                    'path': cls.polymorphic_primary_key_name
                },
                'properties': cls.get_mapping_properties()
            }
        }

    @classmethod
    def get_mapping_properties(cls):
        return {
            'polymorphic_ctype': {'type': 'integer'},
            cls.polymorphic_primary_key_name: {'type': 'integer'}
        }

    @classmethod
    def get_mapping_type_name(cls):
        """By default, we'll be using the app_label and module_name properties to get the ES doctype for this object"""
        return "%s_%s" % (cls._meta.app_label, cls._meta.module_name)

    @classmethod
    def get_mapping_type_names(cls):
        """Returns the mapping type name of this class and all of its descendants."""
        names = [cls.get_mapping_type_name()]
        for subclass in cls.__subclasses__():
            names.extend(subclass.get_mapping_type_names())
        return names    

    @classmethod
    def get_index_mappings(cls):
        from collections import defaultdict

        indexes = defaultdict(dict)
        for subclass in cls.__subclasses__():
            sub_indexes = subclass.get_index_mappings()
            for key, value in sub_indexes:
                sub_indexes[key].update(subclass.get_index_mappings())
        return indexes

    def index(self, refresh=False):
        es = get_es(urls=settings.ES_URLS)
        doc = self.extract_document()
        # NOTE: this could be made more efficient with the `doc_as_upsert`
        # param when the following pull request is merged into pyelasticsearch:
        # https://github.com/rhec/pyelasticsearch/pull/132
        es.update(
            self.get_index_name(),
            self.get_mapping_type_name(),
            self.id,
            doc=doc,
            upsert=doc
        )

    def save(self, index=True, refresh=False, *args, **kwargs):
        result = super(PolymorphicIndexable, self).save(*args, **kwargs)
        if index:
            self.index(refresh=refresh)
        self._index = index
        return result

