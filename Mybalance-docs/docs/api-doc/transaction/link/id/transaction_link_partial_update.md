
----------------------------------------------------------------------------------
## transaction link partial update
* Endpoint: `PATCH v1/transaction/link/:id`
* Purpose: Approve or Reject an escrow transaction

## Authorization

```json
API key
```

## Path Variables
id                          "string"(Required)

> Body parameter
```json
{
  "status": "REJECTED",
  "rejectedReason": [
    "WRONG_DESCRIPTION",
    "WRONG_DESCRIPTION"
  ]
}
```

> 200 Response

```json
{
  "status": "REJECTED",
  "rejectedReason": [
    "WRONG_DESCRIPTION",
    "WRONG_DESCRIPTION"
  ]
}
```
-----------------------------------------------------------------------------