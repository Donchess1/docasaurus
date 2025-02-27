
----------------------------------------------------------------------------------
## console overview transactions list
* Endpoint: `POST /merchants/customers/initiate-withdrawal`
* Purpose: Initiate withdrawal from seller dashboard

##Authorization

```json
API Key
```

> Body parameter

```json
{
  "amount": "<integer>",
  "currency": "NGN",
  "bankCode": "<string>",
  "accountNumber": "<string>",
  "merchantId": "<uuid>"
}
```
> 200 Response

```json
 {
  "amount": "<integer>",
  "currency": "NGN",
  "bankCode": "<string>",
  "accountNumber": "<string>",
  "merchantId": "<uuid>"
}
```
----------------------------------------------------------------------------------