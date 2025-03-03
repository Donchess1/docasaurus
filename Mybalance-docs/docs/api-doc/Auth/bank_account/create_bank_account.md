
----------------------------------------------------------------------------------
## Create Bank Accounts
* Endpoint: `POST /v1/auth/bank-accounts`
* Purpose: Extracts user's back details by id.

## Authorization

```json
API key
```

> Body parameter
```json
{
  "bank_code": "string",
  "account_number": "string",
}
```
> 201 Response

```json
{
  "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
  "user_id": 0,
  "bank_name": "string",
  "bank_code": "string",
  "account_name": "string",
  "account_number": "string",
  "is_default": false,
  "created_at": "2019-08-24T14:15:22Z",
  "updated_at": "2019-08-24T14:15:22Z"
}
```
----------------------------------------------------------------------------------