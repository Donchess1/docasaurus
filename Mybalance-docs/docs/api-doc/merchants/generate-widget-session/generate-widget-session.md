
----------------------------------------------------------------------------------
## merchants generate-widget-session create
* Endpoint: `GET v1/merchants/generate-widget-session`
* Purpose: Generate Customer Widget Session URL

## Authorization

```json
API key
```
## Query Params
status                  completed
tx_ref                  "string"
transaction_id          "string"

> Body parameter
```json
{
  "customerEmail": "<email>"
}
```

> 200 Response

```json
{
  "widgetUrl": "<uri>",
  "sessionLifetime": "<string>"
}
```
-----------------------------------------------------------------------------