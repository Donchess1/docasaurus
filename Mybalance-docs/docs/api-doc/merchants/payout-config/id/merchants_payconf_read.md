
----------------------------------------------------------------------------------
## merchants payout-config read
* Endpoint: `GET v1/merchants/payout-config/:id/`
* Purpose: 

## Authorization

```json
API key
```

Path Variables
```json
id                          <uuid>(Required)A UUID string identifying this payout config.
```

> Body parameter
```json

```

> 200 Response

```json
{
  "name": "<string>",
  "id": "<uuid>",
  "merchant": "<uuid>",
  "buyerChargeType": "FLAT_FEE",
  "buyerAmount": "<string>",
  "sellerChargeType": "FLAT_FEE",
  "sellerAmount": "<string>",
  "isActive": "<boolean>",
  "createdAt": "<dateTime>",
  "updatedAt": "<dateTime>"
}
```
----------------------------------------------------------------------------------