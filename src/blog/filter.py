from .models import BlogPost
import django_filters
from django_filters import rest_framework as django_filters

class BlogFilter(django_filters.FilterSet):
    is_archived = django_filters.BooleanFilter(field_name="is_archived")
    created_at = django_filters.DateFromToRangeFilter(field_name="created_at")
   # tags = django_filters.CharFilter(field_name="tags", lookup_expr="icontains")
    is_draft = django_filters.BooleanFilter(field_name="is_draft")
    
    class Meta:
        model = BlogPost
        fields = ["is_archived", "created_at", "is_draft"]
        
