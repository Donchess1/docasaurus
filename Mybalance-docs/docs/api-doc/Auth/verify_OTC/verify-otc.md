
----------------------------------------------------------------------------------
## Verify created account
* Endpoint:`POST /auth/verify-otc`
* Purpose: Verify accounts 

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