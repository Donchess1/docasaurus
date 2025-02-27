
----------------------------------------------------------------------------------
## console transactions activity-logs list
* Endpoint: `PATCH v1/console/transactions?status=<string>&created=<string>&type=<string>&reference=<string>&provider=MYBALANCE&currency=<string>&email=<string>&mode=<string>&amount_lt=<string>&amount_gt=<string>&amount_lte=<string>&amount_gte=<string>&amount_exact=<string>&search=<string>&ordering=<string>&page=<integer>&size=<integer>`
* Purpose: 

##Authorization

```json
API Key
```
## Query Params

```json
status
<string>
status

created
<string>
created

type
<string>
type

reference
<string>
reference

provider
MYBALANCE
provider

currency
<string>
currency

email
<string>
email

mode
<string>
mode

amount_lt
<string>
amount_lt

amount_gt
<string>
amount_gt

amount_lte
<string>
amount_lte

amount_gte
<string>
amount_gte

amount_exact
<string>
amount_exact

search
<string>
A search term.

ordering
<string>
Which field to use when ordering the results.

page
<integer>
A page number within the paginated result set.

size
<integer>
Number of results to return per page.
```

> Body parameter
```json
{

}
```

> 200 parameter

```json
{
  "count": "<integer>",
  "results": [
    {
      "status": "PENDING",
      "id": "<uuid>",
      "userId": "<integer>",
      "type": "DEPOSIT",
      "mode": "<string>",
      "reference": "<string>",
      "narration": "<string>",
      "amount": "<integer>",
      "charge": "<integer>",
      "remittedAmount": "<integer>",
      "currency": "NGN",
      "provider": "BLUSALT",
      "providerTxReference": "<string>",
      "meta": {},
      "verified": "<boolean>",
      "merchant": "<uuid>",
      "lockedAmount": "<string>",
      "escrowMetadata": "<string>",
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    },
    {
      "status": "EXPIRED",
      "id": "<uuid>",
      "userId": "<integer>",
      "type": "DEPOSIT",
      "mode": "<string>",
      "reference": "<string>",
      "narration": "<string>",
      "amount": "<integer>",
      "charge": "<integer>",
      "remittedAmount": "<integer>",
      "currency": "USD",
      "provider": "FLUTTERWAVE",
      "providerTxReference": "<string>",
      "meta": {},
      "verified": "<boolean>",
      "merchant": "<uuid>",
      "lockedAmount": "<string>",
      "escrowMetadata": "<string>",
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    }
  ],
  "next": "<uri>",
  "previous": "<uri>"
}
```

> 200 Response

```json
{
  "status": "CANCELLED",
  "id": "<uuid>",
  "userId": "<integer>",
  "type": "MERCHANT_SETTLEMENT",
  "mode": "<string>",
  "reference": "<string>",
  "narration": "<string>",
  "amount": "<integer>",
  "charge": "<integer>",
  "remittedAmount": "<integer>",
  "currency": "NGN",
  "provider": "BLUSALT",
  "providerTxReference": "<string>",
  "meta": {},
  "verified": "<boolean>",
  "merchant": "<uuid>",
  "lockedAmount": "<string>",
  "escrowMetadata": "<string>",
  "createdAt": "<dateTime>",
  "updatedAt": "<dateTime>"
}
```
----------------------------------------------------------------------------------