
----------------------------------------------------------------------------------
## shared trim-merchant-token create
* Endpoint: `POST v1/shared/trim-merchant-token`
* Purpose: Deconstruct Merchant Widget Token

## Authorization

```json
API key
```

> Body parameter
```json
{
  "key": "<string>"
}
```

> 200 Response

```json
{
  "token": "<string>",
  "merchantId": "<uuid>"
}
```
-----------------------------------------------------------------------------