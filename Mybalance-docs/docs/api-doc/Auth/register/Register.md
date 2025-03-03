
----------------------------------------------------------------------------------
## Create user
* Endpoint: POST /auth/register
* Purpose: Creates a new user account in the MyBalance platform. This step is required before accessing other services.

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