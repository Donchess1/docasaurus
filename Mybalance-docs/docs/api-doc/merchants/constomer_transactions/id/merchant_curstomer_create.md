
----------------------------------------------------------------------------------
## merchants customer-transactions create
* Endpoint: `POST v1/merchants/customer-transactions/{id}`
* Purpose: Create dispute for merchant escrow transaction.

##Authorization

```json
API Key
```

> Body parameter

```json
{
  "priority": "LOW",
  "reason": "bad quality",
  "description": "Over 24hrs and goods not delivered yet"
}
```

```json
{
  "priority": "HIGH",
  "reason": "<string>",
  "description": "<string>",
  "id": "<uuid>",
  "transaction": "<uuid>",
  "author": "BUYER",
  "buyer": "<integer>",
  "seller": "<integer>",
  "status": "PENDING",
  "meta": {},
  "createdAt": "<dateTime>",
  "updatedAt": "<dateTime>"
}
```
----------------------------------------------------------------------------------