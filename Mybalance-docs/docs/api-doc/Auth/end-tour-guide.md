
----------------------------------------------------------------------------------
* Endpoint:`PUT /v1/auth/end-tour-guide
* Purpose: Create a tour guide account for user.

```json
{
  "userId": "<integer>",
  "userType": "MERCHANT",
  "avatar": "<uri>",
  "profileLink": "<uri>",
  "freeEscrowTransactions": "<integer>",
  "phoneNumberFlagged": "<boolean>",
  "showTourGuide": "<boolean>",
  "lastLoginDate": "<dateTime>",
  "bankAccountId": "<uuid>",
  "businessId": "<uuid>",
  "kycId": "<uuid>",
  "isFlagged": "<boolean>",
  "isDeactivated": "<boolean>"
}
```
> 200 Response

```json
{
  "userId": "<integer>",
  "userType": "BUYER",
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
```
----------------------------------------------------------------------------------