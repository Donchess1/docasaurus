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
