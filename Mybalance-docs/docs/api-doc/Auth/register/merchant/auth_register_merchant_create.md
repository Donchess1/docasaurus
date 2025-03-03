
----------------------------------------------------------------------------------
## Create Merchant
* Endpoint: `POST /auth/register/merchant
* Purpose: Creates a new merchant's account in the MyBalance platform. This step is required before accessing merchants' based services.

## Authorization
```json
API key
```

> Body parameter

```json
{
  "first_name": "string",
  "last_name": "string",
  "email": "user@example.com",
  "phone": "string",
  "password": "string",
  "merchant_name": "string",
  "description": "string",
  "address": "string",
  "buyer_charge_type": "PERCENTAGE",
  "seller_charge_type": "PERCENTAGE",
  "buyer_amount": 0,
  "seller_amount": 0
}
```

> 201 Create  Response
```json
{
   "firstName": "<string>",
  "lastName": "<string>",
  "email": "<email>",
  "phone": "03834500021",
  "password": "<string>",
  "merchantName": "<string>",
  "description": "<string>",
  "address": "<string>",
  "buyerChargeType": "FLAT_FEE",
  "sellerChargeType": "FLAT_FEE",
  "buyerAmount": "<integer>",
  "sellerAmount": "<integer>",
  "id": "<integer>"
}
```
----------------------------------------------------------------------------------