import os

from django.contrib.auth import get_user_model
from rest_framework import status

from console import tasks as console_tasks
from console.models.transaction import LockedAmount, Transaction
from core.resources.flutterwave import FlwAPI
from core.resources.sockets.pusher import PusherSocket
from notifications.models.notification import UserNotification
from transaction import tasks as txn_tasks
from utils.activity_log import log_transaction_activity
from utils.text import notifications
from utils.utils import add_commas_to_transaction_amount, parse_datetime

User = get_user_model()
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "")
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "")


def handle_withdrawal(data, request_meta, pusher):
    amount_charged = data.get("amount")
    msg = data.get("complete_message")
    amount_to_debit = data["meta"].get("amount_to_debit")
    customer_email = data["meta"].get("customer_email")
    tx_ref = data["meta"].get("tx_ref")

    try:
        txn = Transaction.objects.get(reference=tx_ref)
    except Transaction.DoesNotExist:
        return {
            "success": False,
            "message": "Transaction does not exist",
            "status_code": status.HTTP_404_NOT_FOUND,
        }

    if txn.verified:
        # Occasionally, Flutterwave might send the same webhook event more than once.
        # This is to make this event processing idempotent.
        # So calling the webhook multiple times will have the same effect.
        # We don't want to end up debit customer multiple times.
        # At the same time, Flutterwave acknowledges receipt of the webhook when we return 200 HTTP status code
        return {
            "success": False,
            "message": "Transaction already verified",
            "status_code": status.HTTP_200_OK,
        }

    if data["status"] == "FAILED":
        txn.status = "FAILED"
        txn.meta.update({"note": msg})
        txn.verified = True
        txn.save()

        description = f"Withdrawal failed. Description: {msg}"
        log_transaction_activity(txn, description, request_meta)

        pusher.trigger(
            f"WALLET_WITHDRAWAL_{tx_ref}",
            "WALLET_WITHDRAWAL_FAILURE",
            {
                "status": "FAILED",
                "message": msg,
                "amount": txn.amount,
                "currency": txn.currency,
            },
        )

        return {
            "success": True,
            "message": "Webhook processed successfully.",
            "status_code": status.HTTP_200_OK,
        }

    description = f"Withdrawal of {txn.currency} {add_commas_to_transaction_amount(amount_to_debit)} was completed successfuly and verified via WEBHOOK."
    log_transaction_activity(txn, description, request_meta)

    user = User.objects.filter(email=customer_email).first()
    _, wallet = user.get_currency_wallet(txn.currency)
    description = f"Previous Balance: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
    log_transaction_activity(txn, description, request_meta)

    user.debit_wallet(amount_to_debit, txn.currency)
    user.update_withdrawn_amount(amount=txn.amount, currency=txn.currency)

    _, wallet = user.get_currency_wallet(txn.currency)
    description = f"New Balance: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
    log_transaction_activity(txn, description, request_meta)

    pusher.trigger(
        f"WALLET_WITHDRAWAL_{tx_ref}",
        "WALLET_WITHDRAWAL_SUCCESS",
        {
            "status": "SUCCESSFUL",
            "message": msg,
            "amount": txn.amount,
            "currency": txn.currency,
        },
    )

    txn.status = "SUCCESSFUL"
    txn.meta.update({"note": msg})
    txn.verified = True
    txn.save()

    email = user.email
    values = {
        "first_name": user.name.split(" ")[0],
        "recipient": email,
        "transaction_reference": (txn.reference).upper(),
        "amount_withdrawn": f"{txn.currency} {add_commas_to_transaction_amount(txn.amount)}",
        "date": parse_datetime(txn.created_at),
        "bank_name": data.get("bank_name"),
        "account_name": data.get("fullname"),
        "account_number": data.get("account_number"),
    }
    console_tasks.send_wallet_withdrawal_email.delay(email, values)
    UserNotification.objects.create(
        user=user,
        category="WITHDRAWAL",
        title=notifications.WalletWithdrawalNotification(
            txn.amount, txn.currency
        ).TITLE,
        content=notifications.WalletWithdrawalNotification(
            txn.amount, txn.currency
        ).CONTENT,
        action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{tx_ref}",
    )

    return {
        "success": True,
        "message": "Webhook processed successfully.",
        "status_code": status.HTTP_200_OK,
    }


def handle_deposit(data, request_meta, pusher):
    tx_ref = data.get("tx_ref")
    flw_transaction_id = data.get("id")

    try:
        txn = Transaction.objects.get(reference=tx_ref)
    except Transaction.DoesNotExist:
        return {
            "success": False,
            "message": "Transaction does not exist",
            "status_code": status.HTTP_404_NOT_FOUND,
        }

    if txn.verified:
        # Occasionally, Flutterwave might send the same webhook event more than once.
        # This is to make this event processing idempotent.
        # So calling the webhook multiple times will have the same effect.
        # We don't want to end up debit customer multiple times.
        # At the same time, Flutterwave acknowledges receipt of the webhook when we return 200 HTTP status code
        return {
            "success": False,
            "message": "Transaction already verified",
            "status_code": status.HTTP_200_OK,
        }

    if data["status"] != "successful":
        txn.status = "FAILED"
        txn.meta.update({"note": msg})
        txn.verified = True
        txn.save()

        description = f"Payment failed."
        log_transaction_activity(txn, description, request_meta)

        return {
            "success": True,
            "message": "Deposit webhook processed successfully.",
            "status_code": status.HTTP_200_OK,
        }

    obj = FlwAPI.verify_transaction(flw_transaction_id)
    print("============================================================")
    print("============================================================")
    print("VERIFYING FLW DEPOSIT TRANSACTION")
    print(obj)
    print("============================================================")
    print("============================================================")
    if obj["status"] == "error":
        msg = obj["message"]
        txn.meta.update({"description": f"FLW Transaction {msg}"})
        txn.save()

        description = f"Error occurred while verifying transaction. Description: {msg}"
        log_transaction_activity(txn, description, request_meta)

        # TODO: Log this error in observability service: Tag [FLW Err:]
        return {
            "success": False,
            "message": f"{msg}",
            "status_code": status.HTTP_400_BAD_REQUEST,
        }

    if obj["data"]["status"] == "failed":
        msg = obj["data"]["processor_response"]
        txn.meta.update({"description": f"FLW Transaction {msg}"})
        txn.save()

        description = f"Transaction failed. Description: {msg}"
        log_transaction_activity(txn, description, request_meta)

        # TODO: Log this error in observability service: Tag ["FLW Failed:]
        return {
            "success": False,
            "message": f"{msg}",
            "status_code": status.HTTP_200_OK,
        }

    if (
        obj["data"]["tx_ref"] == txn.reference
        and obj["data"]["status"] == "successful"
        and obj["data"]["currency"] == txn.currency
        and obj["data"]["charged_amount"] >= txn.amount
    ):
        data = obj["data"]
        flw_ref = data.get("flw_ref")
        narration = data.get("narration")
        txn.verified = True
        txn.status = "SUCCESSFUL"
        txn.mode = data.get("auth_model")
        txn.charge = data.get("app_fee")
        txn.remitted_amount = data.get("amount_settled")
        txn.provider_tx_reference = flw_ref
        txn.narration = narration
        payment_type = obj["data"]["payment_type"]
        txn.meta.update(
            {
                "payment_method": payment_type,
                "provider_txn_id": obj["data"]["id"],
                "description": f"FLW Transaction {narration}_{flw_ref}",
            }
        )
        txn.save()
        amount_charged = data.get("charged_amount")
        msg = data.get("processor_response")
        tx_ref = data.get("tx_ref")
        flw_transaction_id = data.get("id")
        customer_email = data["customer"].get("email")
        meta = data.get("meta")

        description = f"Payment received via {payment_type} channel. Transaction verified via WEBHOOK."
        log_transaction_activity(txn, description, request_meta)

        try:
            user = User.objects.filter(email=customer_email).first()
        except User.DoesNotExist:
            return {
                "success": True,
                "message": "User does not exist.",
                "status_code": status.HTTP_404_NOT_FOUND,
            }

        wallet_exists, wallet = user.get_currency_wallet(txn.currency)
        description = f"Previous Balance: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
        log_transaction_activity(txn, description, request_meta)

        user.credit_wallet(txn.amount, txn.currency)
        # Now we need to know if the purpose of this deposit is to fund wallet or fund escrow
        escrow_transaction_reference = meta.get("escrow_transaction_reference", None)
        if escrow_transaction_reference:
            escrow_txn = Transaction.objects.filter(
                reference=escrow_transaction_reference
            ).first()
            escrow_txn.verified = True
            escrow_txn.status = "SUCCESSFUL"
            escrow_txn.save()
            escrow_amount_to_charge = int(escrow_txn.amount + escrow_txn.charge)

            _, wallet = user.get_currency_wallet(txn.currency)
            description = f"Balance after topup: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
            log_transaction_activity(txn, description, request_meta)

            profile = user.userprofile
            buyer_free_escrow_credits = int(profile.free_escrow_transactions)
            escrow_credits_used = False
            if buyer_free_escrow_credits > 0:
                # deplete free credits and make transaction free
                profile.free_escrow_transactions -= 1
                profile.save()
                escrow_amount_to_charge = escrow_txn.amount
                escrow_credits_used = True

            user.debit_wallet(escrow_amount_to_charge, txn.currency)

            _, wallet = user.get_currency_wallet(txn.currency)
            description = f"New Balance after final debit: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
            log_transaction_activity(txn, description, request_meta)

            user.update_locked_amount(
                amount=escrow_txn.amount,
                currency=escrow_txn.currency,
                mode="OUTWARD",
                type="CREDIT",
            )

            # =================================================================
            # ESCROW TRANSACTION ACTIVITY
            escrow_credits_message = " " if escrow_credits_used else " not "
            description = (
                f"{escrow_txn.currency} {add_commas_to_transaction_amount(escrow_txn.amount)} was locked successfully by buyer: {(user.name).upper()} <{user.email}> via direct wallet debit. Escrow credit was"
                + escrow_credits_message
                + f"used by buyer."
            )
            log_transaction_activity(escrow_txn, description, request_meta)
            # ESCROW TRANSACTION ACTIVITY
            # =================================================================

            instance = LockedAmount.objects.create(
                transaction=escrow_txn,
                user=user,
                seller_email=(
                    escrow_txn.escrowmeta.partner_email
                    if escrow_txn.escrowmeta.author == "BUYER"
                    else escrow_txn.user_id.email
                ),
                amount=escrow_txn.amount,
                status="ESCROW",
            )
            escrow_amount = add_commas_to_transaction_amount(escrow_txn.amount)
            buyer_values = {
                "first_name": user.name.split(" ")[0],
                "recipient": user.email,
                "date": parse_datetime(escrow_txn.updated_at),
                "amount_funded": f"{txn.currency} {escrow_amount}",
                "transaction_id": escrow_txn.reference,
                "item_name": escrow_txn.meta["title"],
                # "seller_name": seller.name,
            }
            # We only notify seller at this point if they initiated the transaction.
            # If the buyer initiated, then the seller will be notified after they approve the transaction.
            # This may not be immediate. Seller may take a while to approve the transaction.
            # So we just default to use the created_at timestamp on LockedAmount instance above as time to avoid incorrect timestamps when email is sent out
            if escrow_txn.escrowmeta.author == "SELLER":
                seller = escrow_txn.user_id
                seller.update_locked_amount(
                    amount=escrow_txn.amount,
                    currency=escrow_txn.currency,
                    mode="INWARD",
                    type="CREDIT",
                )

                seller_values = {
                    "first_name": seller.name.split(" ")[0],
                    "recipient": seller.email,
                    "date": parse_datetime(escrow_txn.updated_at),
                    "amount_funded": f"{escrow_txn.currency} {escrow_amount}",
                    "transaction_id": escrow_txn.reference,
                    "item_name": escrow_txn.meta["title"],
                    "buyer_name": user.name,
                }
                txn_tasks.send_lock_funds_seller_email.delay(
                    seller.email, seller_values
                )
                # Create Notification for Seller
                UserNotification.objects.create(
                    user=seller,
                    category="FUNDS_LOCKED_SELLER",
                    title=notifications.FundsLockedSellerNotification(
                        escrow_amount, escrow_txn.currency
                    ).TITLE,
                    content=notifications.FundsLockedSellerNotification(
                        escrow_amount, escrow_txn.currency
                    ).CONTENT,
                    action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{escrow_txn_ref}",
                )

            txn_tasks.send_lock_funds_buyer_email.delay(user.email, buyer_values)
            #  Create Notification for Buyer
            UserNotification.objects.create(
                user=user,
                category="FUNDS_LOCKED_BUYER",
                title=notifications.FundsLockedBuyerNotification(
                    escrow_amount, escrow_txn.currency
                ).TITLE,
                content=notifications.FundsLockedBuyerNotification(
                    escrow_amount, escrow_txn.currency
                ).CONTENT,
                action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{escrow_transaction_reference}",
            )
        else:
            _, wallet = user.get_currency_wallet(txn.currency)
            description = f"New Balance: {txn.currency} {add_commas_to_transaction_amount(wallet.balance)}"
            log_transaction_activity(txn, description, request_meta)
            email = user.email
            values = {
                "first_name": user.name.split(" ")[0],
                "recipient": email,
                "date": parse_datetime(txn.created_at),
                "amount_funded": f"{txn.currency} {add_commas_to_transaction_amount(txn.amount)}",
                "wallet_balance": f"{txn.currency} {add_commas_to_transaction_amount(wallet.balance)}",
                "transaction_reference": f"{(txn.reference).upper()}",
            }
            console_tasks.send_fund_wallet_email.delay(email, values)
            # Create Notification
            UserNotification.objects.create(
                user=user,
                category="DEPOSIT",
                title=notifications.WalletDepositNotification(
                    txn.amount, txn.currency
                ).TITLE,
                content=notifications.WalletDepositNotification(
                    txn.amount, txn.currency
                ).CONTENT,
                action_url=f"{BACKEND_BASE_URL}/v1/transaction/link/{tx_ref}",
            )
        return {
            "success": False,
            "status_code": status.HTTP_200_OK,
            "message": "Transaction verified.",
        }
