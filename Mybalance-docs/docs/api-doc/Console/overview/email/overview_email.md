
----------------------------------------------------------------------------------
## GET console overview emails list
* Endpoint: `GET /console/overview/emails`
* Purpose: Generate api key for merchants

##Authorization

```json
API Key
```

> Body parameter

```json
{
  
}
```
> 200 Response

```json
  [
  {
    "period": "<string>",
    "startDate": "<dateTime>",
    "endDate": "<dateTime>",
    "total": "<integer>",
    "buyers": "<integer>",
    "sellers": "<integer>",
    "merchants": "<integer>",
    "admins": "<integer>"
  },
  {
    "period": "<string>",
    "startDate": "<dateTime>",
    "endDate": "<dateTime>",
    "total": "<integer>",
    "buyers": "<integer>",
    "sellers": "<integer>",
    "merchants": "<integer>",
    "admins": "<integer>"
  }
]

```
----------------------------------------------------------------------------------