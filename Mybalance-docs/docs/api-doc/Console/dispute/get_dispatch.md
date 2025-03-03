
----------------------------------------------------------------------------------
## Update disputes by id
* Endpoint: `GET /console/disputes?priority=<string>&source=<string>&status=<string>&author=<string>&created=<string>&email=<string>&search=<string>&ordering=<string>&page=<integer>&size=<integer>`
* Purpose: .

## Authorization
```json
API key
```

## Query Params
```json
priority<string>            priority

source<string>              source  

status<string>              status

author<string>              author

created<string>             created

email<string>               email

search<string>              A search term.

ordering<string>            Which field to use when ordering the results.

page<integer>               A page number within the paginated result set.

size  <integer>             Number of results to return per page.
```

> Body parameter

```json
{}
```
> 200 Response

```json
{
  "transaction": "<uuid>",
  "priority": "MEDIUM",
  "reason": "<string>",
  "description": "<string>",
  "id": "<uuid>",
  "author": "SELLER",
  "buyer": "<integer>",
  "seller": "<integer>",
  "status": "PROGRESS",
  "meta": {},
  "createdAt": "<dateTime>",
  "updatedAt": "<dateTime>"
}
```
----------------------------------------------------------------------------------