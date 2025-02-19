
----------------------------------------------------------------------------------
## Create Bank Accounts
* Endpoint: `POST /v1/auth/bank-accounts`
* Purpose: Extracts user's back details by id.

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

## Get Merchant's Costomer's accounts
* Endpoint:`GET /v1/auth/bank-accounts`
* Purpose: Extracts merchant's customers accounts.
To perform this operation, you must be authenticated by means of one of the following methods:
jwtAuth

> 200 Response

```json
[
   {
    "bankCode": "<string>",
    "accountNumber": "<string>",
    "id": "<uuid>",
    "userId": "<integer>",
    "bankName": "<string>",
    "accountName": "<string>",
    "isActive": "<boolean>",
    "createdAt": "<dateTime>",
    "updatedAt": "<dateTime>"
  },
  {
    "bankCode": "<string>",
    "accountNumber": "<string>",
    "id": "<uuid>",
    "userId": "<integer>",
    "bankName": "<string>",
    "accountName": "<string>",
    "isActive": "<boolean>",
    "createdAt": "<dateTime>",
    "updatedAt": "<dateTime>"
  }
]
```
----------------------------------------------------------------------------------


To perform this operation, you must be authenticated by means of one of the following methods:
jwtAuth

## 

`GET /v1/auth/bank-accounts/{id}`

> 200 Response

```json
{
  "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
  "user_id": 0,
  "bank_name": "string",
  "bank_code": "string",
  "account_name": "string",
  "account_number": "stringstri",
  "is_default": false,
  "created_at": "2019-08-24T14:15:22Z",
  "updated_at": "2019-08-24T14:15:22Z"
}
```
----------------------------------------------------------------------------------
To perform this operation, you must be authenticated by means of one of the following methods:
jwtAuth

## v1_auth_bank_accounts_update

> Code samples
* Endpoint:`PUT /v1/auth/bank-accounts/{id}`
* Purpose: Extracts user's back details by id.

> Body parameter

```json
{
  "bank_code": "string",
  "account_number": "stringstri",
  "is_default": false
}
```

> 200 Response

```json
{
  "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
  "user_id": 0,
  "bank_name": "string",
  "bank_code": "string",
  "account_name": "string",
  "account_number": "stringstri",
  "is_default": false,
  "created_at": "2019-08-24T14:15:22Z",
  "updated_at": "2019-08-24T14:15:22Z"
}
```

----------------------------------------------------------------------------------


----------------------------------------------------------------------------------