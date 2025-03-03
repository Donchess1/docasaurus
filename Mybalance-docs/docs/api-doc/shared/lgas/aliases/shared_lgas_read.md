
----------------------------------------------------------------------------------
## 
* Endpoint: `GET v1/shared/lgas/:alias`
* Purpose: Retrieve Local Government Areas (LGA) by State Alias

## Authorization

```json
API key
```

## Path Variables
```json

alias                   <string>(Required)
```

> Body parameter
```json
{ }
```

> 200 Response

```json
{
  "lgas": [
    "<string>",
    "<string>"
  ]
}
```
-----------------------------------------------------------------------------