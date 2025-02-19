
----------------------------------------------------------------------------------
## Resets Password
* Endpoint: `PUT /auth/reset-password`
* Purpose: Resets user's password.

> Body parameter

```json
{
  "hash": "<string>",
  "password": "<string>",
  "confirmPassword": "<string>"
}
```
> 200 Response

```json
 {
  "hash": "<string>",
  "password": "<string>",
  "confirmPassword": "<string>"
}
```
----------------------------------------------------------------------------------