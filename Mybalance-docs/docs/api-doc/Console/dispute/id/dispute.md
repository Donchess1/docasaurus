
----------------------------------------------------------------------------------
## Resets Password
* Endpoint: `GET /console/disputes/:id`
* Purpose: .

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