
----------------------------------------------------------------------------------
## merchants payout-config list
* Endpoint: `GET v1/merchants/payout-config/`
* Purpose: 

## Authorization

```json
API key
```

> Body parameter
```json

```

> 200 Response

```json
[
  {
    "name": "<string>",
    "id": "<uuid>",
    "merchant": "<uuid>",
    "buyerChargeType": "NO_FEES",
    "buyerAmount": "<string>",
    "sellerChargeType": "PERCENTAGE",
    "sellerAmount": "<string>",
    "isActive": "<boolean>",
    "createdAt": "<dateTime>",
    "updatedAt": "<dateTime>"
  },
  {
    "name": "<string>",
    "id": "<uuid>",
    "merchant": "<uuid>",
    "buyerChargeType": "NO_FEES",
    "buyerAmount": "<string>",
    "sellerChargeType": "FLAT_FEE",
    "sellerAmount": "<string>",
    "isActive": "<boolean>",
    "createdAt": "<dateTime>",
    "updatedAt": "<dateTime>"
  }
]
```
----------------------------------------------------------------------------------