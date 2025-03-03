
----------------------------------------------------------------------------------
## merchants dashboard customer-disputes list
* Endpoint: `GET v1/merchants/dashboard/customer-disputes?priority=<string>&source=<string>&status=<string>&author=<string>&created=<string>&email=<string>&search=<string>&page=<integer>&size=<integer>`
* Purpose: 

##Authorization

```json
API Key
```
##Query Params
```json
priority<string>            priority

source<string>              source

status<string>              status

author<string>              author

created<string>             created

email<string>               email

search<string>              A search term.

page<integer>               A page number within the paginated result set.

size<integer>               Number of results to return per page.
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
      "transaction": "<uuid>",
      "priority": "HIGH",
      "reason": "<string>",
      "description": "<string>",
      "id": "<uuid>",
      "author": "SELLER",
      "buyer": "<integer>",
      "seller": "<integer>",
      "status": "PENDING",
      "meta": {},
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    },
    {
      "transaction": "<uuid>",
      "priority": "LOW",
      "reason": "<string>",
      "description": "<string>",
      "id": "<uuid>",
      "author": "BUYER",
      "buyer": "<integer>",
      "seller": "<integer>",
      "status": "PENDING",
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