from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from console.models import Transaction


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def process_pending_transactions(self):
    try:
        one_hour_ago = timezone.now() - timedelta(hours=3)
        # Fetch the IDs of pending transactions that have been pending for over 3 hours, limit to 50
        pending_transaction_ids = Transaction.objects.filter(
            status="PENDING", type="DEPOSIT", created_at__lt=one_hour_ago
        ).values_list('id', flat=True)[:50]

        if not pending_transaction_ids:
            return

        # Update the status of these transactions to EXPIRED in bulk
        Transaction.objects.filter(id__in=pending_transaction_ids).update(status="EXPIRED")

    except Exception as e:
        # Retry the task if an error occurs
        raise self.retry(exc=e)
