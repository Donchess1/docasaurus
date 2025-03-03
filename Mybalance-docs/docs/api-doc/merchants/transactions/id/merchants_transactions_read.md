_
----------------------------------------------------------------------------------
## merchants profile-info partial update
* Endpoint: `GET v1/merchants/transactions/60083ba8-11b1-454b-ad3f-659a7b85010c`
* Purpose: 

## Authorization

```json
Bearer Token
```

> Body parameter
```json
{  }
```

> 200 Response

```json
{
  "status": "APPROVED",
  "id": "<uuid>",
  "type": "WITHDRAW",
  "mode": "<string>",
  "reference": "<string>",
  "amount": "<integer>",
  "charge": "<integer>",
  "currency": "USD",
  "meta": {},
  "customerRole": "<string>",
  "verified": "<boolean>",
  "escrow": "<string>",
  "createdAt": "<dateTime>",
  "updatedAt": "<dateTime>"
}
```
----------------------------------------------------------------------------------