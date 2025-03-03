
----------------------------------------------------------------------------------
## Send OTC
* Endpoint:`POST /auth/generate-otc`
* Purpose: Sends a One time Login to password to user

## Authorization
```json
API key
```

> Body parameter

```json
  {
  "email": "<email>"
}
  ```

> 200 Response

```json
 {
  "email": "<email>"
}
```
----------------------------------------------------------------------------------