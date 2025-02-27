
----------------------------------------------------------------------------------
## console users deactivate
* Endpoint: `PATCH v1/console/users/:id/flag/`
* Purpose: 

##Authorization

```json
API Key
```
## Query Params

```json
id                  <uuid> (Required)
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