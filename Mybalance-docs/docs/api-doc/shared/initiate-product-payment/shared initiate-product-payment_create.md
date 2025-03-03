
----------------------------------------------------------------------------------
## shared fund-wallet-terraswitch create
* Endpoint: `POST v1/shared/initiate-product-payment`
* Purpose: 

## Authorization

```json
API key
```

> Body parameter
```json
{
  "productReference": "<string>",
  "quantity": "<integer>",
  "useFlatFee": true
}
```

> 200 Response

```json
{
  "productReference": "<string>",
  "quantity": "<integer>",
  "useFlatFee": true
}
```
-----------------------------------------------------------------------------