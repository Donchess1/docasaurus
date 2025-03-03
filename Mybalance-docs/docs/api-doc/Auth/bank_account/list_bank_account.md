
----------------------------------------------------------------------------------
## Get Merchant's Costomer's accounts

* Endpoint:`GET /v1/auth/bank-accounts`
* Purpose: Extracts merchant's customers accounts.

## Authorization
```json
API key
```

> 200 Response

```json
[
   {
    "bankCode": "<string>",
    "accountNumber": "<string>",
    "id": "<uuid>",
    "userId": "<integer>",
    "bankName": "<string>",
    "accountName": "<string>",
    "isActive": "<boolean>",
    "createdAt": "<dateTime>",
    "updatedAt": "<dateTime>"
  },
  {
    "bankCode": "<string>",
    "accountNumber": "<string>",
    "id": "<uuid>",
    "userId": "<integer>",
    "bankName": "<string>",
    "accountName": "<string>",
    "isActive": "<boolean>",
    "createdAt": "<dateTime>",
    "updatedAt": "<dateTime>"
  }
]
```
----------------------------------------------------------------------------------