
----------------------------------------------------------------------------------

## GET USER PROFILE

* Endpoint: GET /auth/profile
* Purpose: Retrieve User's details


> Body parameter

```json

```

> 200 Response

```json
[
  {
    "userId": "<integer>",
    "userType": "CUSTOM",
    "id": "<uuid>",
    "avatar": "<uri>",
    "profileLink": "<uri>",
    "freeEscrowTransactions": "<integer>",
    "phoneNumberFlagged": "<boolean>",
    "createdAt": "<dateTime>",
    "updatedAt": "<dateTime>",
    "showTourGuide": "<boolean>",
    "lastLoginDate": "<dateTime>",
    "bankAccountId": "<uuid>",
    "businessId": "<uuid>",
    "kycId": "<uuid>",
    "isFlagged": "<boolean>",
    "isDeactivated": "<boolean>",
    "unreadNotificationCount": "<string>"
  },
  {
    "userId": "<integer>",
    "userType": "SELLER",
    "id": "<uuid>",
    "avatar": "<uri>",
    "profileLink": "<uri>",
    "freeEscrowTransactions": "<integer>",
    "phoneNumberFlagged": "<boolean>",
    "createdAt": "<dateTime>",
    "updatedAt": "<dateTime>",
    "showTourGuide": "<boolean>",
    "lastLoginDate": "<dateTime>",
    "bankAccountId": "<uuid>",
    "businessId": "<uuid>",
    "kycId": "<uuid>",
    "isFlagged": "<boolean>",
    "isDeactivated": "<boolean>",
    "unreadNotificationCount": "<string>"
  }
]
```
----------------------------------------------------------------------------------
