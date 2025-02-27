## notification app get notification details
* Endpoint: `GET v1/notifications/`
* Purpose: Retrieve details of a specific notification.

## Authorization

```json
API Key
```

## Path Params

```json
search<string>                A search term.
page<integer>                 A page number within the paginated result set.

size
<integer>
Number of results to return per page.
```

> Body parameter

```json
{}
```

> 200 Response

```json
{
  "count": "<integer>",
  "results": [
    {
      "user": "<integer>",
      "category": "WITHDRAWAL",
      "content": "<string>",
      "id": "<uuid>",
      "title": "<string>",
      "isSeen": "<boolean>",
      "actionUrl": "<uri>",
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    },
    {
      "user": "<integer>",
      "category": "ESCROW_APPROVED",
      "content": "<string>",
      "id": "<uuid>",
      "title": "<string>",
      "isSeen": "<boolean>",
      "actionUrl": "<uri>",
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>"
    }
  ],
  "next": "<uri>",
  "previous": "<uri>"
}
```
