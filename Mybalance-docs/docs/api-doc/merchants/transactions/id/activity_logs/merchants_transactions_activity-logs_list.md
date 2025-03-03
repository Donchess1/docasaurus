
----------------------------------------------------------------------------------
## merchants profile-info partial update
* Endpoint: `GET v1/merchants/settlements?status=<string>&created=<string>&type=<string>&reference=<string>&provider=MYBALANCE&currency=<string>&email=<string>&mode=<string>&amount_lt=<string>&amount_gt=<string>&amount_lte=<string>&amount_gte=<string>&amount_exact=<string>&search=<string>&page=<integer>&size=<integer>`
* Purpose: 

## Authorization

```json
API key
```
## Path Variables
```json
id                            "string" Required
```

> Body parameter
```json
{  }
```

> 200 Response

```json
[
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
```
----------------------------------------------------------------------------------