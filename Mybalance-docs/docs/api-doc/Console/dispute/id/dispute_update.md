
----------------------------------------------------------------------------------
## Update disputes by id
* Endpoint: `PUT /console/disputes/:id`
* Purpose: .

## Authorization
```json
API key
```

> Body parameter

```json
{
  "destination": "BUYER",
  "supportingDocument": "<uri>",
  "supportingNote": "<string>"
}
```
> 200 Response

```json
{
  "destination": "BUYER",
  "supportingDocument": "<uri>",
  "supportingNote": "<string>"
}
```
----------------------------------------------------------------------------------