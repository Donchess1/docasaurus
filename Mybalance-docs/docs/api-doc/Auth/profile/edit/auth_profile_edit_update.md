
----------------------------------------------------------------------------------
## PROFILE DETAILS UPDATE
* Endpoint: PUT /auth/profile/edit
* Purpose: Upload Business details


## Authorization
```json
API key
```

> Body parameter
```json
{
  "name": "<string>",
  "email": "<email>",
  "phone": "32882171205",
  "isVerified": "<boolean>",
  "isBuyer": "<boolean>",
  "isSeller": "<boolean>",
  "isMerchant": "<boolean>",
  "isAdmin": "<boolean>"
}
```

> 201 Response

```json
{
  "name": "<string>",
  "email": "<email>",
  "id": "<integer>",
  "phone": "49731590135",
  "isVerified": "<boolean>",
  "isBuyer": "<boolean>",
  "isSeller": "<boolean>",
  "isMerchant": "<boolean>",
  "isAdmin": "<boolean>",
  "metadata": "<string>",
  "createdAt": "<dateTime>",
  "updatedAt": "<dateTime>"
}
```
----------------------------------------------------------------------------------
