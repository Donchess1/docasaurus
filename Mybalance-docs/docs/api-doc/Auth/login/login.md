
----------------------------------------------------------------------------------
## login
* Endpoint: `POST /v1/auth/login`
* Purpose: Login User


> Body parameter
```json
{
  "email": "<email>",
  "password": "<string>"
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
    "phone": "47200920762",
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