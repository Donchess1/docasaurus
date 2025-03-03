
----------------------------------------------------------------------------------
## unlock-funds
* Endpoint: `POST v1/transaction/unlock-funds`
* Purpose: Unlock funds for a Escrow Transaction as a Buyer

## Authorization

```json
Bearer Token
```

> Body parameter
```json
{
  "transactionReference": "FE5KU1QHK20250205121923"
}
```

> 200 Response

```json
{
  "status": "CANCELLED",
  "id": "<uuid>",
  "userId": "<integer>",
  "type": "MERCHANT_SETTLEMENT",
  "mode": "<string>",
  "reference": "<string>",
  "narration": "<string>",
  "amount": "<integer>",
  "charge": "<integer>",
  "remittedAmount": "<integer>",
  "currency": "NGN",
  "provider": "BLUSALT",
  "providerTxReference": "<string>",
  "meta": {},
  "verified": "<boolean>",
  "merchant": "<uuid>",
  "lockedAmount": "<string>",
  "escrowMetadata": "<string>",
  "createdAt": "<dateTime>",
  "updatedAt": "<dateTime>"
}
```
-----------------------------------------------------------------------------