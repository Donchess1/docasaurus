
----------------------------------------------------------------------------------
## console disputes read
* Endpoint: `GET /console/disputes/:id`
* Purpose: Get a dispute detail by ID

## Authorization
```json
API key
```

## Path Variables
```json
id                      <string>(Required)
```

> Body parameter

```json
{ }
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