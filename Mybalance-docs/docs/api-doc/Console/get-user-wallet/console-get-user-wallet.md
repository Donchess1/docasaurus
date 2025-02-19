
----------------------------------------------------------------------------------
## User's General Events
* Endpoint: `POST /v1//console/get-user-wallet`
* Purpose: .

> Body parameter

```json
{
  "email": "<email>"
}
```
> 200 Response

```json
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
```
----------------------------------------------------------------------------------