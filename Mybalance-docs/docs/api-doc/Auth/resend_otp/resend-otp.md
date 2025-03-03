
----------------------------------------------------------------------------------
## Resend OTP
* Endpoint: `POST /auth/resend-otp`
* Purpose: Resends OTP to users.

## Authorization
```json
API key
```

> Body parameter

```json
  {
  "email": "<email>",
  "oldTempId": "<string>"
}
```

> 200 Response

```json
 {
  "tempId": "<string>",
  "email": "<email>"
}

```
----------------------------------------------------------------------------------