
----------------------------------------------------------------------------------
## merchants disputes read
* Endpoint: `GET v1/merchants/escrow-redirect?status=completed&tx_ref=UGL6Z7I8020250205222355&transaction_id=8368566`
* Purpose: 

## Authorization

```json
API key
```
## Query Params
status                  <completed>
tx_ref                  <string>
transaction_id          <string>

> Body parameter
```json

```

> 200 Response

```json
[
  {
    "transactionReference": "<string>",
    "amount": "<integer>",
    "redirectUrl": "<uri>"
  },
  {
    "transactionReference": "<string>",
    "amount": "<integer>",
    "redirectUrl": "<uri>"
  }
]
```
-----------------------------------------------------------------------------