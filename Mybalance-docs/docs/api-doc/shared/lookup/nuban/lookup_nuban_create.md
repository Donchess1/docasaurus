
----------------------------------------------------------------------------------
## shared lookup nuban create
* Endpoint: `POST v1/shared/lookup/nuban`
* Purpose: Verify Bank Account

## Authorization

```json
API key
```

> Body parameter
```json
{
  "bankCode": "<string>",
  "accountNumber": "<string>"
}
```

> 200 Response

```json
{
  "nuban": "<string>",
  "accountName": "<string>",
  "identityType": "<string>",
  "bank": "<string>",
  "accountCurrency": "<string>"
}
```
-----------------------------------------------------------------------------