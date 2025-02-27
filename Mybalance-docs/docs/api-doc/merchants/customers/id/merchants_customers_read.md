
----------------------------------------------------------------------------------
## merchants customers read
* Endpoint: `GET /merchants/customers/:id`
* Purpose: 

##Authorization

```json
API Key
```

##Path Variables
```json
id                <string>(Required)
```

> Body parameter

```json
{
}
```
> 200 Response

```json
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
```
----------------------------------------------------------------------------------