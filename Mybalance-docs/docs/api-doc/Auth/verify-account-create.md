
----------------------------------------------------------------------------------
## Verify created account
* Endpoint:`POST /auth/verify-account`
* Purpose: Verify created accounts

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