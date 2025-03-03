
----------------------------------------------------------------------------------
## BUSINESS DETAILS UPDATE
* Endpoint: PUT /auth/profile/business
* Purpose: Upload Business details

## Authorization
```json
API key
```

> Body parameter
```json
{
  "name": "<string>",
  "address": "<string>",
  "description": "<string>",
  "phone": "09723618279"
}
```

> 201 Response

```json
{
  "name": "<string>",
  "address": "<string>",
  "description": "<string>",
  "id": "<uuid>",
  "userId": "<integer>",
  "phone": "15681205385",
  "createdAt": "<dateTime>",
  "updatedAt": "<dateTime>"
}
```
----------------------------------------------------------------------------------
