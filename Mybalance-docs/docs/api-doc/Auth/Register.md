
----------------------------------------------------------------------------------

## AUTHENTICATION ENDPOINTS
```json
## BASE_URL:

staging - `https://api.staging.mybalance.com/v1/` 
```

## Create user
* Endpoint: POST /auth/register
* Purpose: Creates a new user account in the MyBalance platform. This step is required before accessing other services.


> Body parameter

```json
{
  "first_name": "string",
  "last_name": "string",
  "email": "user@example.com",
  "phone": "string",
  "referrer": "OTHERS",
  "password": "string"
}
```

> 201 Response

```json
{
  "id": 0,
  "first_name": "string",
  "last_name": "string",
  "email": "user@example.com",
  "phone": "string",
  "referrer": "OTHERS",
  "is_buyer": true,
  "is_seller": true,
  "is_verified": true
}
```
----------------------------------------------------------------------------------

## Create Merchant

* Endpoint: `POST /auth/register/merchant
* Purpose: Creates a new merchant's account in the MyBalance platform. This step is required before accessing merchants' based services.

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

> 201 Response
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

## Create seller
* Endpoint: `POST /auth/register/seller`
* Purpose: Creates a new merchant's account in the MyBalance platform. This step is required before accessing merchants' based services.

> Body parameter

```json
{
  "first_name": "string",
  "last_name": "string",
  "email": "user@example.com",
  "phone": "string",
  "password": "string",
  "referrer": "OTHERS",
  "business_name": "string",
  "business_description": "string",
  "address": "string",
  "bank_name": "string",
  "bank_code": "string",
  "account_number": "string",
  "account_name": "string"
}
```
> 201 Response

```json
{
  "id": 0,
  "first_name": "string",
  "last_name": "string",
  "email": "user@example.com",
  "phone": "string",
  "is_buyer": true,
  "referrer": "OTHERS",
  "is_seller": true,
  "is_verified": true,
  "business_name": "string",
  "business_description": "string",
  "address": "string",
  "bank_name": "string",
  "bank_code": "string",
  "account_number": "string",
  "account_name": "string"
}
```
----------------------------------------------------------------------------------

## Login user

* Endpoint: `POST /auth/login`
* Purpose: Logs in users into their MyBalance platform account.
* To perform this operation, you must be authenticated by jwtAuth

> Body parameter

```json
{
  "email": "user@example.com",
  "password": "string"
}
```
> 200 Response
```json
{
  "token": "<string>",
  "user": {
    "name": "<string>",
    "email": "<email>",
    "id": "<integer>",
    "phone": "83750205015",
    "isVerified": "<boolean>",
    "isBuyer": "<boolean>",
    "isSeller": "<boolean>",
    "isMerchant": "<boolean>",
    "isAdmin": "<boolean>",
    "metadata": "<string>",
    "createdAt": "<dateTime>",
    "updatedAt": "<dateTime>"
  }
}
```
----------------------------------------------------------------------------------