from django.db.models import Q
from django_filters import rest_framework as django_filters

from console.models.transaction import Transaction


class TransactionFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    created = django_filters.DateFromToRangeFilter(field_name="created_at")
    type = django_filters.CharFilter(field_name="type", lookup_expr="iexact")
    currency = django_filters.CharFilter(field_name="currency", lookup_expr="iexact")
    email = django_filters.CharFilter(method="filter_by_user_email")
    # user_id = django_filters.CharFilter(method="filter_by_user_id")

    class Meta:
        model = Transaction
        fields = [
            "status",
            "created",
            "type",
            "reference",
            "provider",
            "currency",
            "email",
        ]

    def filter_by_user_email(self, queryset, name, value):
        # Filtering for transactions where the user is either the main user or involved in escrow
        return queryset.filter(
            Q(user_id__email=value)
            | Q(escrowmeta__partner_email=value)
            | Q(escrowmeta__meta__parties__buyer=value)
            | Q(escrowmeta__meta__parties__seller=value)
        ).distinct()

    def filter_by_user_id(self, queryset, name, value):
        # Custom logic for filtering by user_id
        # this is an expensive operation so it's not recommended to use it
        # TODO: escrowmeta__meta__parties__buyer & escrowmeta__meta__parties__seller actually resolve to email string
        return queryset.filter(
            Q(user_id__id=value)
            # | Q(escrowmeta__partner_id=value)
            | Q(escrowmeta__meta__parties__buyer_id=value)
            | Q(escrowmeta__meta__parties__seller_id=value)
        ).distinct()
