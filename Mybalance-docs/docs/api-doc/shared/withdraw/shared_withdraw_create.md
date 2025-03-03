
----------------------------------------------------------------------------------
## shared withdraw create
* Endpoint: `POST v1/shared/withdraw`
* Purpose: 

## Authorization

```json
API key
```

> Body parameter
```json
{
  "amount": "<integer>",
  "bankCode": "<string>",
  "accountNumber": "<string>",
  "currency": "NGN",
  "description": "<string>"
}
```

> 200 Response

```json
{
  "amount": "<integer>",
  "bankCode": "<string>",
  "accountNumber": "<string>",
  "currency": "NGN",
  "description": "<string>"
}
```
-----------------------------------------------------------------------------