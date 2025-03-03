
----------------------------------------------------------------------------------
## forgot-password
* Endpoint: `POST /v1/auth/forgot-password`
* Purpose: Request to reset User Password

## Authorization
```json
API key
```

> Body parameter

```json
{
  "email": "<email>",
  "platform": "BASE_PLATFORM"
}
```
> 201 Response

```json
{
  "email": "<email>",
  "platform": "BASE_PLATFORM"
}
```
----------------------------------------------------------------------------------