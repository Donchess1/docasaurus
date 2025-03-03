
----------------------------------------------------------------------------------
## shared lookup nin create
* Endpoint: `GET v1/shared/lookup/nin`
* Purpose: Verify National Identification Number (NIN)

## Authorization

```json
API key
```

> Body parameter
```json
{
  "number": "<string>"
}
```

> 200 Response

```json
{
  "nin": "<string>",
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