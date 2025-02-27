
----------------------------------------------------------------------------------
## console transactions activity-logs list
* Endpoint: `PATCH v1/console/transactions/:id`
* Purpose: 

##Authorization

```json
API Key
```
## Query Params

```json
id                  <uuid> (Required)
```

> Body parameter

```json
{
  "reason": "<string>",
  "supportingDocument": "<uri>"
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
----------------------------------------------------------------------------------