from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet

from console.models import Dispute

User = get_user_model()


def get_user_owned_dispute_queryset(user: User) -> QuerySet[Dispute]:
    # Disputes where user is the author or recipient
    queryset = (
        Dispute.objects.filter(Q(buyer=user) | Q(seller=user))
        .order_by("-created_at")
        .distinct()
    )
    return queryset
