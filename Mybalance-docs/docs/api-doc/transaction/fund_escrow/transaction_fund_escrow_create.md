## transaction fund-escrow create
* Endpoint: `POST v1/fund-escrow`
* Purpose: Fund escrow transaction with Payment Gateway

## Authorization

```json
API Key
```


> Body parameter

```json
{
  "transactionReference": "<string>",
  "amountToCharge": "<integer>"
}
```

> 200 Response

```json
{
  "transactionReference": "<string>",
  "amountToCharge": "<integer>"
}
```
