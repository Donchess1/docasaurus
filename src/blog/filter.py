import django_filters
from django_filters import rest_framework as django_filters

from .models import BlogPost


class BlogFilter(django_filters.FilterSet):
    is_archived = django_filters.BooleanFilter(field_name="is_archived")
    tags = django_filters.CharFilter(method="filter_tags")
    created = django_filters.DateFromToRangeFilter(field_name="created_at")
    is_draft = django_filters.BooleanFilter(field_name="is_draft")

    class Meta:
        model = BlogPost
        fields = ["is_archived", "created", "is_draft"]

    def filter_tags(self, queryset, name, value):
        """
        Custom filter to handle a list of tags.
        Splits the provided tags by comma, making each tag case-insensitive.
        """
        tags_list = [tag.strip().upper() for tag in value.split(",")]
        for tag in tags_list:
            queryset = queryset.filter(tags__name__iexact=tag)
        return queryset
