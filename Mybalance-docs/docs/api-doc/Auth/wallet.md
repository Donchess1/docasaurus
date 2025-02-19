
----------------------------------------------------------------------------------
## Wallets
* Endpoint:`GET /auth/wallets`
* Purpose: Get user's wallet

> Body parameter

```json
  
  ```

> 200 Response

```json
[
  {
    "currency": "NGN",
    "id": "<uuid>",
    "balance": "<string>",
    "lockedAmountOutward": "<string>",
    "lockedAmountInward": "<string>",
    "unlockedAmount": "<string>",
    "withdrawnAmount": "<string>",
    "createdAt": "<dateTime>",
    "updatedAt": "<dateTime>"
  },
  {
    "currency": "NGN",
    "id": "<uuid>",
    "balance": "<string>",
    "lockedAmountOutward": "<string>",
    "lockedAmountInward": "<string>",
    "unlockedAmount": "<string>",
    "withdrawnAmount": "<string>",
    "createdAt": "<dateTime>",
    "updatedAt": "<dateTime>"
  }
]
```
----------------------------------------------------------------------------------