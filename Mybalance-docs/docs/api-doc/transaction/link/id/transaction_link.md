
----------------------------------------------------------------------------------
## transaction link read
* Endpoint: `GET v1/transaction/link/:id`
* Purpose: Get a transaction detail by ID or Reference

## Authorization

```json
API key
```

## Path Variables
id "string"                           (Required)

> Body parameter
```json
{ }
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