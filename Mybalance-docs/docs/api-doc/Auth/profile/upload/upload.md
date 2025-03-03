
----------------------------------------------------------------------------------
## UPLOAD IMAGES

* Endpoint: POST /auth/profile/upload
* Purpose: Upload Images


## Authorization
```json
API key
```

> Body parameter

```json
{
  "destination": "AVATAR"
}
```

> 201 Response

```json
{
  "image": "<uri>",
  "destination": "AVATAR"
}
```
----------------------------------------------------------------------------------
