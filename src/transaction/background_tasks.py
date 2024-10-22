from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from console.models import Transaction


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def process_pending_transactions(self):
    try:
        # Calculate the threshold for pending transactions
        one_hour_ago = timezone.now() - timedelta(hours=1)

        # Fetch pending transactions that have been in pending state for over an hour
        pending_transactions = Transaction.objects.filter(
            status="PENDING", created_at__lt=one_hour_ago
        )[
            :50
        ]  # Limit to 500 transactions

        if not pending_transactions:
            return

        # Update the status of these transactions to TIMED_OUT in bulk
        Transaction.objects.filter(
            id__in=pending_transactions.values_list("id", flat=True)
        ).update(status="EXPIRED")

    except Exception as e:
        # Retry the task if an error occurs
        raise self.retry(exc=e)
