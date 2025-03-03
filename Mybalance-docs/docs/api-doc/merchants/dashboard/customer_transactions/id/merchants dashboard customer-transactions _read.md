
----------------------------------------------------------------------------------
## merchants dashboard customer-transactions list
* Endpoint: `GET v1/merchants/dashboard/customer-transactions?status=<string>&created=<string>&type=<string>&reference=<string>&provider=MYBALANCE&currency=<string>&email=<string>&mode=<string>&amount_lt=<string>&amount_gt=<string>&amount_lte=<string>&amount_gte=<string>&amount_exact=<string>&search=<string>&page=<integer>&size=<integer>`
* Purpose: 

## Authorization
```json
API key
```

Path Variables
```json
id "string"                     (Required)
```

## Query Params
```json
priority "string"            priority

source "string"              source

status "string"              status

author "string"              author

created "string"             created

email "string"               email

search "string"              A search term.

page "integer"               A page number within the paginated result set.

size "integer"               Number of results to return per page.
```

> Body parameter

```json
{ }
```
Body parameter
```json
  "count": "<integer>",
  "results": [
    {
      "status": "EXPIRED",
      "id": "<uuid>",
      "type": "PRODUCT",
      "mode": "<string>",
      "reference": "<string>",
      "amount": "<integer>",
      "charge": "<integer>",
      "currency": "NGN",
      "meta": {},
      "customerRole": "<string>",
      "verified": "<boolean>",
      "escrow": "<string>",
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    },
    {
      "status": "FAILED",
      "id": "<uuid>",
      "type": "MERCHANT_SETTLEMENT",
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
  ],
  "next": "<uri>",
  "previous": "<uri>"
```
----------------------------------------------------------------------------------