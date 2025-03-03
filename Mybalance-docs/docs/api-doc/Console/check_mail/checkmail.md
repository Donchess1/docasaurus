
----------------------------------------------------------------------------------
## Resets Password
* Endpoint: `POST /console/check-email`
* Purpose: 

## Authorization
```json
API key
```

> Body parameter

```json
{
  "email": "<email>"
}
```
> 200 Response

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