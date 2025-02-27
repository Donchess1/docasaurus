## notification app get notification details
* Endpoint: `GET v1/notifications/:id`
* Purpose: Retrieve details of a specific notification.

## Authorization

```json
API Key
```

## Path Params

```json
id                  <uuid> (Required)
```

> Body parameter

```json
{}
```

> 200 Response

```json
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
```
