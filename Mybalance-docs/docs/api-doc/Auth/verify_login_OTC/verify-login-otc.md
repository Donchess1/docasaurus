
----------------------------------------------------------------------------------
## Verify created account
* Endpoint:`POST /auth//verify-login-otc`
* Purpose: Verify accounts based on one time login credentials

## Authorization
```json
API key
```

> Body parameter

```json
  {
  "otp": "string",
  "tempId": "string"
}
  ```

> 200 Response

```json
 {
  "email": "<email>"
}
```
----------------------------------------------------------------------------------