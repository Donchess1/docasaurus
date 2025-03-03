
----------------------------------------------------------------------------------
## merchants disputes read
* Endpoint: `GET v1/merchants/disputes/:id`
* Purpose: 

## Authorization

```json
API key
```
Path Variables
```json
id<string>                  (Required)
```

> Body parameter
```json

```

> 200 Response

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