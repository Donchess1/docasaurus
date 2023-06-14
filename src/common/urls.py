from django.urls import path

from common.views.banks import ListBanksView, ValidateBankAccountView
from common.views.bvn import ValidateBVNView
from common.views.driver_license import ValidateDriverLicenseView
from common.views.fund_wallet import FundWalletCallbackView, FundWalletView
from common.views.nin import ValidateNINView
from common.views.passport import ValidatePassportView
from common.views.state_lga import ListLGAByStateAliasView, ListNGNStatesView
from common.views.voter_card import ValidateVoterCardView

urlpatterns = [
    path("banks", ListBanksView.as_view(), name="list-banks"),
    path("states", ListNGNStatesView.as_view(), name="list-ngn-states"),
    path("lgas/<str:alias>", ListLGAByStateAliasView.as_view(), name="list-state-lgas"),
    path("lookup/nin", ValidateNINView.as_view(), name="validate-nin"),
    path("lookup/bvn", ValidateBVNView.as_view(), name="validate-bvn"),
    path(
        "lookup/voter-card", ValidateVoterCardView.as_view(), name="validate-voter-card"
    ),
    path(
        "lookup/driver-license",
        ValidateDriverLicenseView.as_view(),
        name="validate-driver-license",
    ),
    path(
        "lookup/passport",
        ValidatePassportView.as_view(),
        name="validate-international-passport",
    ),
    path(
        "lookup/nuban",
        ValidateBankAccountView.as_view(),
        name="validate-bank-account",
    ),
    path(
        "deposit-money",
        FundWalletView.as_view(),
        name="deposit-money",
    ),
    path(
        "payment-callback",
        FundWalletCallbackView.as_view(),
        name="deposit-money",
    ),
]
