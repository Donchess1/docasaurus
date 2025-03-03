
----------------------------------------------------------------------------------
## Verify Email Address
* Endpoint: `POST v1/shared/lookup/email`
* Purpose: 

## Authorization

```json
API key
```

> Body parameter
```json
{
  "email": "<email>"
}
```

> 200 Response

```json
{
  "email": "<string>",
  "firstName": "<string>",
  "middleName": "<string>",
  "lastName": "<string>",
  "telephoneno": "<string>",
  "profession": "<string>",
  "title": "<string>",
  "birthdate": "<string>",
  "birthstate": "<string>",
  "birthcountry": "<string>"
}
```
-----------------------------------------------------------------------------