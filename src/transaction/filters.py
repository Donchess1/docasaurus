from django_filters import rest_framework as django_filters

from console.models.transaction import Transaction


class TransactionFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    created = django_filters.DateFromToRangeFilter(field_name="created_at")
    type = django_filters.CharFilter(field_name="type", lookup_expr="iexact")

    class Meta:
        model = Transaction
        fields = ["status", "created", "type", "reference", "provider"]
