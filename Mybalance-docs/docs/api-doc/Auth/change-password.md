
----------------------------------------------------------------------------------
* Endpoint:`PUT /v1/auth/change-password`
* Purpose: Change user's password.
To perform this operation, you must be authenticated by means of one of the following methods:
jwtAuth


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

----------------------------------------------------------------------------------