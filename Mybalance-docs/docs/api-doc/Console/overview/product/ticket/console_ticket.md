
----------------------------------------------------------------------------------
## console products get all product tickets
* Endpoint: `GET /console/products/tickets/?search=<string>&page=<integer>&size=<integer>`
* Purpose: 

##Authorization

```json
API Key
```

## Query Params

```json
search<string>      A search term.

page<integer>       A page number within the paginated result set.

size<integer>       Number of results to return per page.
```
> Body parameter

```json
{
  
}
```
> 200 Response

```json
  {
  "count": "<integer>",
  "results": [
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
    },
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
  ],
  "next": "<uri>",
  "previous": "<uri>"
}
```
----------------------------------------------------------------------------------