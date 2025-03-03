_
----------------------------------------------------------------------------------
## merchants payout-config list
* Endpoint: `POST v1/merchants/payout-config/`
* Purpose: 

## Authorization

```json
API key
```

> Body parameter
```json
{
  "name": "<string>",
  "buyerChargeType": "NO_FEES",
  "buyerAmount": "<string>",
  "sellerChargeType": "FLAT_FEE",
  "sellerAmount": "<string>"
}
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