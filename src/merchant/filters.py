from datetime import datetime, time

from django.db.models import Q
from django_filters import rest_framework as django_filters

from merchant.models import Merchant


class MerchantFilter(django_filters.FilterSet):
    created = django_filters.DateFromToRangeFilter(field_name="created_at")
    email = django_filters.CharFilter(method="filter_by_user_email")
    name = django_filters.CharFilter(field_name="name", lookup_expr="iexact")

    class Meta:
        model = Merchant
        fields = ["name", "email", "created"]

    def filter_by_user_email(self, queryset, name, value):
        return queryset.filter(Q(user_id__email=value)).distinct()
