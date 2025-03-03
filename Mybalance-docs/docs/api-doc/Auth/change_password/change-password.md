
----------------------------------------------------------------------------------
## change-password
* Endpoint:`PUT /v1/auth/change-password`
* Purpose: Change user's password.

## Authorization
```json
API key
```

> Body parameter

```json
{
  "current_password": "string",
  "password": "string",
  "confirm_password": "string"
}
```
> 200 Response

```json
{
  "currentPassword": "<string>",
  "password": "<string>",
  "confirmPassword": "<string>"
}
```
----------------------------------------------------------------------------------
