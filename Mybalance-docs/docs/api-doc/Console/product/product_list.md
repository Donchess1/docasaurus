
----------------------------------------------------------------------------------
## console products list
* Endpoint: `GET /v1/console/products/?search=<string>&page=<integer>&size=<integer>`
* Purpose: 

##Authorization

```json
API Key
```

## Query Params

```json
search<string>          A search term.

page<integer>           A page number within the paginated result set.

size<integer>           Number of results to return per page.
```
> Body parameter

```json

```
> 200 Response

```json
  {
  "count": "<integer>",
  "results": [
    {
      "name": "<string>",
      "category": "ITEM",
      "id": "<uuid>",
      "slug": "I",
      "reference": "<string>",
      "description": "<string>",
      "price": "<integer>",
      "currency": "USD",
      "owner": "<integer>",
      "quantity": "<integer>",
      "event": "<uuid>",
      "tier": "<string>",
      "isActive": "<boolean>",
      "meta": {},
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    },
    {
      "name": "<string>",
      "category": "EVENT_TICKET",
      "id": "<uuid>",
      "slug": "gc6y",
      "reference": "<string>",
      "description": "<string>",
      "price": "<integer>",
      "currency": "NGN",
      "owner": "<integer>",
      "quantity": "<integer>",
      "event": "<uuid>",
      "tier": "<string>",
      "isActive": "<boolean>",
      "meta": {},
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    }
  ],
  "next": "<uri>",
  "previous": "<uri>"
}
```
----------------------------------------------------------------------------------