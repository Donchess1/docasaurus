
----------------------------------------------------------------------------------
## User's General Events
* Endpoint: `GET/console/merchants?name=<string>&email=<string>&created=<string>&search=<string>&ordering=<string>&page=<integer>&size=<integer>`
* Purpose: Generate api key for merchants

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
      "name": "<string>",
      "description": "<string>",
      "address": "<string>",
      "id": "<uuid>",
      "owner": "<string>",
      "userId": "<string>",
      "email": "<string>",
      "wallets": "<string>",
      "isActive": "<string>",
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    },
    {
      "name": "<string>",
      "description": "<string>",
      "address": "<string>",
      "id": "<uuid>",
      "owner": "<string>",
      "userId": "<string>",
      "email": "<string>",
      "wallets": "<string>",
      "isActive": "<string>",
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    }
  ],
  "next": "<uri>",
  "previous": "<uri>"
}
```
----------------------------------------------------------------------------------