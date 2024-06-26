class BaseNotification:
    def __init__(self, title, content):
        self.TITLE = title
        self.CONTENT = content


class WalletDepositNotification(BaseNotification):
    def __init__(self, amount, currency):
        TITLE = "Deposit Confirmation"
        CONTENT = f"You deposited {currency} {amount} into your Wallet. Your funds are now securely stored with us. Kindly check your email for more information."
        super().__init__(TITLE, CONTENT)


class WalletWithdrawalNotification(BaseNotification):
    def __init__(self, amount, currency):
        TITLE = "Withdrawal Confirmation"
        CONTENT = f"You withdrew {currency} {amount} from your Wallet. Your requested amount has been processed into your bank account. Kindly check your email for more information."
        super().__init__(TITLE, CONTENT)


class FundsLockedBuyerNotification(BaseNotification):
    def __init__(self, amount, currency):
        TITLE = "Funds Lock Notification"
        CONTENT = f"You have locked {currency} {amount}. This ensures an extra layer of security for your account. Kindly check your email for more information."
        super().__init__(TITLE, CONTENT)


class FundsLockedSellerNotification(BaseNotification):
    def __init__(self, amount, currency):
        TITLE = "Funds Locked Confirmation"
        CONTENT = f"{currency} {amount} has been locked for you. Your account is now more secure with the additional locking feature. Kindly check your email for more information."
        super().__init__(TITLE, CONTENT)


class FundsUnlockedBuyerNotification(BaseNotification):
    def __init__(self, amount, currency):
        TITLE = "Funds Unlock Notification"
        CONTENT = f"You have unlocked {currency} {amount}. Your account is now flexible for further transactions. Kindly check your email for more information."
        super().__init__(TITLE, CONTENT)


class FundsUnlockedSellerNotification(BaseNotification):
    def __init__(self, amount, currency):
        TITLE = "Funds Unlocked Confirmation"
        CONTENT = f"{currency} {amount} has been unlocked for you. You now have full access to your account for transactions. Kindly check your email for more information."
        super().__init__(TITLE, CONTENT)


ESCROW_TRANSACTION_APPROVED_TITLE = "Transaction Approved"
ESCROW_TRANSACTION_APPROVED_CONTENT = "Your transaction has been approved. Thank you for choosing MyBalance for your financial transactions. Kindly check your email for more information."

ESCROW_TRANSACTION_REJECTED_TITLE = "Transaction Rejected"
ESCROW_TRANSACTION_REJECTED_CONTENT = "Your transaction has been rejected. Thank you for choosing MyBalance for your financial transactions.Kindly check your email for more information."

DISPUTE_RAISED_NOTIFICATION_TITLE = "Dispute Raised Confirmation"
DISPUTE_RAISED_NOTIFICATION_CONTENT = "You raised a dispute. We are reviewing the matter and will update you shortly. Kindly check your email for more information"

DISPUTE_RESOLUTION_NOTIFICATION_TITLE = "Dispute Resolution Notification"
DISPUTE_RESOLUTION_NOTIFICATION_CONTENT = "Your dispute has been resolved. Thank you for your patience. Kindly check your email for more information. If you have any further concerns, feel free to reach out."
