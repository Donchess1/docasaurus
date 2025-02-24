
----------------------------------------------------------------------------------
## console products create
* Endpoint: `POST v1/console/products/`
* Purpose: 

##Authorization

```json
API Key
```

> Body parameter

```json
{
  "name": "<string>",
  "category": "ITEM",
  "description": "<string>",
  "price": "<integer>",
  "currency": "NGN",
  "quantity": "<integer>",
  "event": "<uuid>",
  "tier": "<string>",
  "isActive": "<boolean>",
  "meta": {}
}
```
> 201 Response

```json
{
  "name": "<string>",
  "category": "EVENT_TICKET",
  "id": "<uuid>",
  "slug": "sSI1FECj",
  "reference": "<string>",
  "description": "<string>",
  "price": "<integer>",
  "currency": "NGN",
  "owner": "<integer>",
  "quantity": "<integer>",
  "event": "<uuid>",
  "tier": "<string>",
  "isActive": "<boolean>",
  "meta": {},
  "createdAt": "<dateTime>",
  "updatedAt": "<dateTime>"
}
```
----------------------------------------------------------------------------------