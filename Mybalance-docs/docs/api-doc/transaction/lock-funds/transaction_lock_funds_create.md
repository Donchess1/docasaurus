
----------------------------------------------------------------------------------
## transaction lock-funds create
* Endpoint: `POST v1/transaction/lock-funds`
* Purpose: Lock funds for escrow transaction as a buyer

## Authorization

```json
API key
```

> Body parameter
```json
{
  "transactionReference": "<string>"
}
```

> 200 Response

```json
{
  "transactionReference": "<string>"
}
```
-----------------------------------------------------------------------------