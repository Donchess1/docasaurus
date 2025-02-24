
----------------------------------------------------------------------------------
## console products get product tickets
* Endpoint: `GET /v1/console/products/:id/tickets/`
* Purpose: 

##Authorization

```json
API Key
```

## Query Params

```json
id                  <uuid>
```
> Body parameter

```json
{
  
}
```
> 200 Response

```json
{
  "ticketCode": "<string>",
  "id": "<uuid>",
  "purchaseDate": "<dateTime>",
  "ticketName": "<string>",
  "name": "<string>",
  "email": "<string>",
  "ticketQuantity": "<string>",
  "amountPaid": "<string>",
  "currency": "<string>"
}
```
----------------------------------------------------------------------------------