from django.db.models import Q
from django_filters import rest_framework as django_filters

from console.models.dispute import Dispute


class DisputeFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    created = django_filters.DateFromToRangeFilter(field_name="created_at")
    priority = django_filters.CharFilter(field_name="priority", lookup_expr="iexact")
    email = django_filters.CharFilter(method="filter_by_user_email")

    class Meta:
        model = Dispute
        fields = [
            "status",
            "created",
            "priority",
            "email",
        ]

    def filter_by_user_email(self, queryset, name, value):
        # Filtering for disputes where the user is either the buyer or the seller
        return queryset.filter(
            Q(buyer__email=value) | Q(seller__email=value)
        ).distinct()
