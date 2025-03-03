
----------------------------------------------------------------------------------
## merchants initiate-customer-withdrawal create
* Endpoint: `POST v1/merchants/initiate-customer-withdrawaltransaction_id=8368566`
* Purpose: 

## Authorization

```json
API key
```

> Body parameter
```json
{
  "email": "<email>",
  "amount": "<integer>",
  "currency": "USD",
  "bankCode": "<string>",
  "accountNumber": "<string>"
}
```

> 200 Response

```json
{
  "email": "<email>",
  "amount": "<integer>",
  "currency": "USD",
  "bankCode": "<string>",
  "accountNumber": "<string>"
}
```
-----------------------------------------------------------------------------