_
----------------------------------------------------------------------------------
## merchants profile-info partial update
* Endpoint: `PATCH v1/merchants/profile-info`
* Purpose: 

## Authorization

```json
Bearer Token
```

> Body parameter
```json
{
  "description": "29, Ladipo Kuku Street. Allen, Ikeja, Lags",
  "address": "ArT Solutions Company",
  "phone": "06681322251",
  "email": "<email>"
}
```

> 200 Response

```json
{
  "description": "<string>",
  "address": "<string>",
  "phone": "06681322251",
  "email": "<email>"
}
```
----------------------------------------------------------------------------------