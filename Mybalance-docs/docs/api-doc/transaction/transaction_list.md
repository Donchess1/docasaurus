
----------------------------------------------------------------------------------
## transaction list
* Endpoint: `POST v1/transaction/?search=<string>&page=<integer>&size=<integer>`
* Purpose: Lock funds for escrow transaction as a buyer

## Authorization

```json
API key
```
## Query Params
```json
search<string>            A search term.
page<integer>             A page number within the paginated result set.
size<integer>             Number of results to return per page.
```

> Body parameter
```json
{ }
```

> 200 Response

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
-----------------------------------------------------------------------------