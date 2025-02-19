
----------------------------------------------------------------------------------
## Verify created account
* Endpoint:`POST /auth/verify-otc`
* Purpose: Verify accounts 

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