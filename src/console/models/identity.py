import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


def validate_number(value):
    value_str = str(value)
    if not value_str.isdigit() or len(value_str) != 11:
        raise ValidationError(
            _("Number must be 11 digits"),
            params={"value": value_str},
        )


class NINIdentity(models.Model):
    PROVIDER = (
        ("ZEEHAFRICA", "ZEEHAFRICA"),
        ("VERIFYME", "VERIFYME"),
        ("MYBALANCE", "MYBALANCE"),
    )
    id = models.UUIDField(
        unique=True, primary_key=True, default=uuid.uuid4, editable=False
    )

    number = models.CharField(
        validators=[validate_number], max_length=11, unique=True, db_index=True
    )
    provider = models.CharField(max_length=255, choices=PROVIDER)
    meta = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.number}"


# provider="MYBALANCE"
number = "01234567890"
meta = {
    "date_of_birth": "1960-11-03",
    "first_name": "OLUWATOSIN",
    "gender": "m",
    "middle_name": "LORDSON",
    "phone_number": "08178135068",
    "last_name": "AYODELE",
    "customer": "266d0439-ff1a-4671-bbeb-1108a3660e36",
}
