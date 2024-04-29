from sendgrid.helpers.mail import TemplateId


class EmailTemplate:
    def __init__(self, environment):
        self.environment = environment
        self.templates = {
            "test": {
                "ACCOUNT_VERIFICATION": TemplateId(
                    "d-4487d3c426ac451ea4107d4622fe5a0f"
                ),
                "ONBOARDING_SUCCESSFUL": TemplateId(
                    "d-e045a73225224c4c83b59ffe6d565bb6"
                ),
                "RESET_PASSWORD": TemplateId("d-6562061135c44c959c43c08e5bc9cc7d"),
                "RESET_PASSWORD_SUCCESSFUL": TemplateId(
                    "d-506c4b99dde94ee7a58d28cf7ba166d3"
                ),
                "WALLET_WITHDRAWAL_SUCCESSFUL": TemplateId(
                    "d-abcbf3f7f9da4a689bc23d04bb25d617"
                ),
                "WALLET_FUNDING_SUCCESSFUL": TemplateId(
                    "d-125b68d79ed148ae84281f37d7cafbf1"
                ),
                "LOCK_FUNDS_BUYER": TemplateId("d-1840ebd4e7ee4281bc18dd8f2b00731e"),
                "LOCK_FUNDS_SELLER": TemplateId("d-0fba8d742e884212ad73b35ed81b9c95"),
                "LOCK_MERCHANT_FUNDS_BUYER": TemplateId(
                    "d-03ca81b85abe4165a5c24cd09c162900"
                ),
                "LOCK_MERCHANT_FUNDS_SELLER": TemplateId(
                    "d-34cc75d6f0d0473fabc7ef8e49dd2ef8"
                ),
                "LOCK_MERCHANT_FUNDS_NOTIFY_MERCHANT": TemplateId(
                    "d-d00a892d52324c5e939dab373e3a58b4"
                ),
                "UNLOCK_FUNDS_BUYER": TemplateId("d-5d1c30c963ad459abeeea4a66172dd35"),
                "UNLOCK_FUNDS_SELLER": TemplateId("d-3c612384a65d44a8b3ee77bfc42dbfff"),
                "UNLOCK_MERCHANT_FUNDS_BUYER": TemplateId(
                    "d-7565ce74fecf4d81b3b0cd3d889900bd"
                ),
                "UNLOCK_MERCHANT_FUNDS_SELLER": TemplateId(
                    "d-6060a6bdbf4c43949ddebca357775f8c"
                ),
                "UNLOCK_MERCHANT_FUNDS_NOTIFY_MERCHANT": TemplateId(
                    "d-974a5b135bb148529ea96a0e96ff2c3d"
                ),
                "ESCROW_TRANSACTION_APPROVED": TemplateId(
                    "d-9fe98b4943a047899d937be276883a98"
                ),
                "ESCROW_TRANSACTION_REJECTED": TemplateId(
                    "d-2a20e467a3994a78a005a0ec9e34ea60"
                ),
                "DISPUTE_RAISED_AUTHOR": TemplateId(
                    "d-d3c1d2fdcb3b483fbad6dfa6154cfec0"
                ),
                "MERCHANT_WIDGET_DISPUTE_RAISED_AUTHOR": TemplateId(
                    "d-76075f2b10e74f95aa31634ae74ecade"
                ),
                "DISPUTE_RAISED_RECIPIENT": TemplateId(
                    "d-56c211aeced24b45bc7f08b4d6e04b1b"
                ),
                "MERCHANT_WIDGET_DISPUTE_RAISED_RECIPIENT": TemplateId(
                    "d-ca505fe977dd4298ba92515cf60c3371"
                ),
                "VERIFY_ONE_TIME_LOGIN_CODE": TemplateId(
                    "d-32e80afb15d34862a9775bd8daac1acd"
                ),
                "MERCHANT_USER_WALLET_WITHDRAWAL_VERIFICATION": TemplateId(
                    "d-40e950255187426e8ae022d96c6b5818"
                ),
            },
            "live": {
                "ACCOUNT_VERIFICATION": TemplateId(
                    "d-c7705c480c644ef69c2599b70f80a796"
                ),
                "ONBOARDING_SUCCESSFUL": TemplateId(
                    "d-8b52dcaa981245ad87f3b736ebf2c47"
                ),
                "RESET_PASSWORD": TemplateId("d-926d624f4ae64585833eda41e0ee1c8c"),
                "RESET_PASSWORD_SUCCESSFUL": TemplateId(
                    "d-60b626bd4fb44d509c19e3621956111c"
                ),
                "WALLET_WITHDRAWAL_SUCCESSFUL": TemplateId(
                    "d-9aeaebb4640245bfb262b1ab1e302d91"
                ),
                "WALLET_FUNDING_SUCCESSFUL": TemplateId(
                    "d-9e264790eb424c6681aaae4f84e3e5a6"
                ),
                "LOCK_FUNDS_BUYER": TemplateId("d-2f55861d9a514831b36ac3ef2b0f484a"),
                "LOCK_FUNDS_SELLER": TemplateId("d-0ef402affb07484487f1661c9c110184"),
                "LOCK_MERCHANT_FUNDS_BUYER": TemplateId(
                    "d-130f161ad7df4c98b01bd74083bfa5a6"
                ),
                "LOCK_MERCHANT_FUNDS_SELLER": TemplateId(
                    "d-2b90268adb8b43ea8478a9a50086609b"
                ),
                "LOCK_MERCHANT_FUNDS_NOTIFY_MERCHANT": TemplateId(
                    "d-9cd182b5ae974993801d8cd3fd5f4c5d"
                ),
                "UNLOCK_FUNDS_BUYER": TemplateId("d-9e19d6d681594f539977f88ab2cc47d8"),
                "UNLOCK_FUNDS_SELLER": TemplateId("d-956b7f285f26463894546fa3df90dd9b"),
                "UNLOCK_MERCHANT_FUNDS_BUYER": TemplateId(
                    "d-3619aaf399924fd1b588c485fd9875ed"
                ),
                "UNLOCK_MERCHANT_FUNDS_SELLER": TemplateId(
                    "d-1f9397453f12439ba4c2798187281fbb"
                ),
                "UNLOCK_MERCHANT_FUNDS_NOTIFY_MERCHANT": TemplateId(
                    "d-86a13ab83d0143cea6cad792205c0623"
                ),
                "ESCROW_TRANSACTION_APPROVED": TemplateId(
                    "d-1ec8ffd0ae1a4bc9a56eb266d35457b7"
                ),
                "ESCROW_TRANSACTION_REJECTED": TemplateId(
                    "d-0911aea76c1f44958c1964997748de2c"
                ),
                "DISPUTE_RAISED_AUTHOR": TemplateId(
                    "d-91c2e16c74eb414ebb9bd0971d70b730"
                ),
                "MERCHANT_WIDGET_DISPUTE_RAISED_AUTHOR": TemplateId(
                    "d-31ebdbec39bf406a87142936fc5510e8"
                ),
                "DISPUTE_RAISED_RECIPIENT": TemplateId(
                    "d-eacabe5d8a294286804688024bf0bcd3"
                ),
                "MERCHANT_WIDGET_DISPUTE_RAISED_RECIPIENT": TemplateId(
                    "d-a21ae21316b144a7b9222aa2090a713a"
                ),
                "VERIFY_ONE_TIME_LOGIN_CODE": TemplateId(
                    "d-900389ba039b4ef4890920267203a11a"
                ),
                "MERCHANT_USER_WALLET_WITHDRAWAL_VERIFICATION": TemplateId(
                    "d-47d95b2d7ea04d70ac7b4ef128e0bd10"
                ),
            },
        }

    def get_template(self, template):
        if (
            self.environment in self.templates
            and template in self.templates[self.environment]
        ):
            return self.templates[self.environment][template]
        else:
            return f"No template found for {template} in {self.environment} environment"
