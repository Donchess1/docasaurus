
----------------------------------------------------------------------------------
## console overview transactions list
* Endpoint: `POST /merchants/customers/unlock-funds?merchant=<string>`
* Purpose: Unlock Escrow Transaction Funds

##Authorization

```json
API Key
```

##Query Params
```json
merchant            <str>
```

> Body parameter

```json
{
  "transactions": [
    "<transaction id>"
  ]
}
```
> 200 Response

```json
 
```
----------------------------------------------------------------------------------