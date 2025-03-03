
----------------------------------------------------------------------------------
## shared payment-redirect list
* Endpoint: `GET v1/shared/lookup/nuban`
* Purpose: Verify Bank Account

## Authorization

```json
API key
```

> Body parameter
```json
{
  
}
```

> 200 Response

```json
[
  {
    "amount": "<integer>",
    "currency": "NGN"
  },
  {
    "amount": "<integer>",
    "currency": "NGN"
  }
]
```
-----------------------------------------------------------------------------