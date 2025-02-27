
----------------------------------------------------------------------------------
## console users get user system metrics
* Endpoint: `GET v1/console/users/:id/system-metrics//`
* Purpose: 

##Authorization

```json
API Key
```
## Query Params

```json
id                  <uuid> (Required)
```

> Body parameter

```json
{
}
```

> 200 Response

```json
{
  "totalTransactions": "<integer>",
  "deposits": "<integer>",
  "withdrawals": "<integer>",
  "escrows": "<integer>",
  "disputes": "<integer>",
  "productPurchases": "<integer>",
  "productSettlements": "<integer>",
  "merchantSettlements": "<integer>"
}
```
----------------------------------------------------------------------------------