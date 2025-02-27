
----------------------------------------------------------------------------------
## merchants dashboard customer-disputes read
* Endpoint: `GET v1/merchants/dashboard/customer-disputes/:id`
* Purpose: 

##Authorization

```json
API Key
```
Path Variables
id                              <string>(Required)

> Body parameter

```json
 {
}
```

```json
{
  "transaction": "<uuid>",
  "priority": "MEDIUM",
  "reason": "<string>",
  "description": "<string>",
  "id": "<uuid>",
  "author": "SELLER",
  "buyer": "<integer>",
  "seller": "<integer>",
  "status": "PROGRESS",
  "meta": {},
  "createdAt": "<dateTime>",
  "updatedAt": "<dateTime>"
}
```
----------------------------------------------------------------------------------