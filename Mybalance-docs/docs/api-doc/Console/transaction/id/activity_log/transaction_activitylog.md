
----------------------------------------------------------------------------------
## console transactions activity-logs list
* Endpoint: `GET v1/console/transactions/60083ba8-11b1-454b-ad3f-659a7b85010c/activity-logs`
* Purpose: 

##Authorization

```json
Bearer Token
Token {{token_Admin}}
```

> Body parameter

> 200 Response
```json
[
  {
    "id": "<integer>",
    "reference": "<string>",
    "type": "<string>",
    "status": "<string>",
    "amount": "<string>",
    "currency": "<string>",
    "logs": [
      {
        "transaction": "<uuid>",
        "description": "<string>",
        "id": "<uuid>",
        "meta": {},
        "createdAt": "<dateTime>",
        "updatedAt": "<dateTime>"
      },
      {
        "transaction": "<uuid>",
        "description": "<string>",
        "id": "<uuid>",
        "meta": {},
        "createdAt": "<dateTime>",
        "updatedAt": "<dateTime>"
      }
    ]
  },
  {
    "id": "<integer>",
    "reference": "<string>",
    "type": "<string>",
    "status": "<string>",
    "amount": "<string>",
    "currency": "<string>",
    "logs": [
      {
        "transaction": "<uuid>",
        "description": "<string>",
        "id": "<uuid>",
        "meta": {},
        "createdAt": "<dateTime>",
        "updatedAt": "<dateTime>"
      },
      {
        "transaction": "<uuid>",
        "description": "<string>",
        "id": "<uuid>",
        "meta": {},
        "createdAt": "<dateTime>",
        "updatedAt": "<dateTime>"
      }
    ]
  }
]
```
----------------------------------------------------------------------------------