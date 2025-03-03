_
----------------------------------------------------------------------------------
## merchants profile-info partial update
* Endpoint: `GET v1/merchants/transaction`
* Purpose: 

## Authorization

```json
Bearer Token
```

> Body parameter
```json
{  }
```

> 200 Response

```json
{
  "count": "<integer>",
  "results": [
    {
      "status": "EXPIRED",
      "id": "<uuid>",
      "type": "PRODUCT",
      "mode": "<string>",
      "reference": "<string>",
      "amount": "<integer>",
      "charge": "<integer>",
      "currency": "NGN",
      "meta": {},
      "customerRole": "<string>",
      "verified": "<boolean>",
      "escrow": "<string>",
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    },
    {
      "status": "FAILED",
      "id": "<uuid>",
      "type": "MERCHANT_SETTLEMENT",
      "mode": "<string>",
      "reference": "<string>",
      "amount": "<integer>",
      "charge": "<integer>",
      "currency": "USD",
      "meta": {},
      "customerRole": "<string>",
      "verified": "<boolean>",
      "escrow": "<string>",
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    }
  ],
  "next": "<uri>",
  "previous": "<uri>"
}
```
----------------------------------------------------------------------------------