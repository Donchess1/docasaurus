class BaseNotification:
    def __init__(self, title, content):
        self.TITLE = title
        self.CONTENT = content


class WalletDepositNotification(BaseNotification):
    def __init__(self, amount):
        TITLE = "Deposit Confirmation"
        CONTENT = f"You deposited {amount} into your Wallet. Your funds are now securely stored with us."
        super().__init__(TITLE, CONTENT)


class WalletWithdrawalNotification(BaseNotification):
    def __init__(self, amount):
        TITLE = "Withdrawal Confirmation"
        CONTENT = f"You withdrew {amount} from your Wallet. Your requested amount has been processed."
        super().__init__(TITLE, CONTENT)


ESCROW_TRANSACTION_APPROVED_TITLE = "Transaction Approved"
ESCROW_TRANSACTION_APPROVED_CONTENT = "Your transaction has been Approved. Thank you for choosing MyBalance for your financial transactions."

ESCROW_TRANSACTION_REJECTED_TITLE = "Transaction Rejected"
ESCROW_TRANSACTION_REJECTED_CONTENT = "Your transaction has been Rejected. Thank you for choosing MyBalance for your financial transactions."

FUNDS_LOCKED_BUYER_TITLE = "Funds Lock Notification"
FUNDS_LOCKED_BUYER_CONTENT = (
    "You have locked funds. This ensures an extra layer of security for your account."
)

FUNDS_LOCKED_CONFIRMATION_TITLE = "Funds Lock Confirmation"
FUNDS_LOCKED_CONFIRMATION_CONTENT = "Funds have been locked for you. Your account is now more secure with the additional locking feature."

FUNDS_UNLOCKED_BUYER_TITLE = "Funds Unlock Notification"
FUNDS_UNLOCKED_BUYER_CONTENT = (
    "You have unlocked funds. Your account is now flexible for further transactions."
)

FUNDS_UNLOCKED_CONFIRMATION_TITLE = "Funds Unlock Confirmation"
FUNDS_UNLOCKED_CONFIRMATION_CONTENT = "Funds have been unlocked for you. You now have full access to your account for transactions."

DISPUTE_RAISED_NOTIFICATION_TITLE = "Dispute Raised Confirmation"
DISPUTE_RAISED_NOTIFICATION_CONTENT = (
    "You raised a dispute. We are reviewing the matter and will update you shortly."
)

DISPUTE_RESOLUTION_NOTIFICATION_TITLE = "Dispute Resolution Notification"
DISPUTE_RESOLUTION_NOTIFICATION_CONTENT = "Your dispute has been resolved. Thank you for your patience. If you have any further concerns, feel free to reach out."
