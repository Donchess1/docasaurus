
----------------------------------------------------------------------------------
## merchants dashboard customer-transactions list
* Endpoint: `GET v1/merchants/disputes`
* Purpose: 

## Authorization

```json
API key
```
> Body parameter
```json

```

> 200 Response

```json
{
  "count": "<integer>",
  "results": [
    {
      "transaction": "<uuid>",
      "priority": "HIGH",
      "reason": "<string>",
      "description": "<string>",
      "id": "<uuid>",
      "author": "SELLER",
      "buyer": "<integer>",
      "seller": "<integer>",
      "status": "PENDING",
      "meta": {},
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    },
    {
      "transaction": "<uuid>",
      "priority": "LOW",
      "reason": "<string>",
      "description": "<string>",
      "id": "<uuid>",
      "author": "BUYER",
      "buyer": "<integer>",
      "seller": "<integer>",
      "status": "PENDING",
      "meta": {},
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    }
  ],
  "next": "<uri>",
  "previous": "<uri>"
}
}
```
----------------------------------------------------------------------------------