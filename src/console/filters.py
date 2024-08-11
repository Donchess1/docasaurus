from datetime import datetime, time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django_filters import rest_framework as django_filters

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    created = django_filters.DateFromToRangeFilter(field_name="created_at")
    type = django_filters.CharFilter(method="filter_by_type")

    class Meta:
        model = User
        fields = ["name", "email", "phone", "created"]

    def filter_by_type(self, queryset, name, value):
        value = value.upper()
        if value == "BUYER":
            return queryset.filter(is_buyer=True)
        elif value == "SELLER":
            return queryset.filter(is_seller=True)
        elif value == "MERCHANT":
            return queryset.filter(is_merchant=True)
        elif value == "ADMIN":
            return queryset.filter(is_admin=True)
        return queryset

    def filter_queryset(self, queryset):
        """
        Override the filter_queryset method to add custom validation and handling for the created filter.
        """
        # Validate date range for the 'created' filter
        created_range = self.data.get("created")
        if created_range:
            start_date, end_date = created_range.split(",")
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

                # Ensure the end_date includes the entire day up to 11:59 PM
                end_date_obj = datetime.combine(end_date_obj, time.max)

                if end_date_obj < start_date_obj:
                    raise ValidationError(
                        "The end date cannot be earlier than the start date."
                    )
            except ValueError:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD.")

            # Apply the filtering using the adjusted start and end dates
            queryset = queryset.filter(created_at__range=(start_date_obj, end_date_obj))

        return super().filter_queryset(queryset)
