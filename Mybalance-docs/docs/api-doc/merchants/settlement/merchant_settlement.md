_
----------------------------------------------------------------------------------
## merchants profile-info partial update
* Endpoint: `GET v1/merchants/settlements?status=<string>&created=<string>&type=<string>&reference=<string>&provider=MYBALANCE&currency=<string>&email=<string>&mode=<string>&amount_lt=<string>&amount_gt=<string>&amount_lte=<string>&amount_gte=<string>&amount_exact=<string>&search=<string>&page=<integer>&size=<integer>`
* Purpose: 

## Authorization

```json
Bearer Token
```
Query Params
status "string"            status

created "string"           created

type "string"              type

reference "string"         reference

providerMYBALANCE         provider

currency "string"          currency

email "string"             email

mode "string"              mode

amount_lt "string"         amount_lt

amount_gt "string"         amount_gt

amount_lte "string"        amount_lte

amount_gte "string"        amount_gte

amount_exact "string"      amount_exact

search "string"            A search term.

page "integer"             A page number within the paginated result set.

size "integer"             Number of results to return per page.

> Body parameter
```json
{  }
```

> 200 Response

```json
{
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
}
```
----------------------------------------------------------------------------------