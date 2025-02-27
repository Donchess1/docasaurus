
----------------------------------------------------------------------------------
## merchants customers list
* Endpoint: `GET v1/merchants/customers`
* Purpose: 

##Authorization

```json
Bearer Token
```

> Body parameter

```json

```

```json
{
  "count": "<integer>",
  "results": [
    {
      "id": "<integer>",
      "userType": "<string>",
      "userId": "<string>",
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>",
      "fullName": "<string>",
      "phoneNumber": "<string>",
      "email": "<string>",
      "wallets": "<string>",
      "systemMetrics": "<string>"
    },
    {
      "id": "<integer>",
      "userType": "<string>",
      "userId": "<string>",
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>",
      "fullName": "<string>",
      "phoneNumber": "<string>",
      "email": "<string>",
      "wallets": "<string>",
      "systemMetrics": "<string>"
    }
  ],
  "next": "<uri>",
  "previous": "<uri>"
}
```
----------------------------------------------------------------------------------