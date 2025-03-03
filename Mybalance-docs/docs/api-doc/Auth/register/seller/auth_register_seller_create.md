
----------------------------------------------------------------------------------
## Create seller
* Endpoint: `POST /auth/register/seller`
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
