
----------------------------------------------------------------------------------
## 
* Endpoint: `POST v1/transaction/initiate-escrow`
* Purpose: 

## Authorization

```json
API key
```

> Body parameter
```json
{
  "purpose": "<string>",
  "itemType": "<string>",
  "itemQuantity": "<integer>",
  "deliveryDate": "<date>",
  "amount": "<integer>",
  "partnerEmail": "<email>",
  "currency": "NGN"
}
```

> 200 Response

```json
{
  "purpose": "<string>",
  "itemType": "<string>",
  "itemQuantity": "<integer>",
  "deliveryDate": "<date>",
  "amount": "<integer>",
  "partnerEmail": "<email>",
  "currency": "NGN"
}
```
-----------------------------------------------------------------------------