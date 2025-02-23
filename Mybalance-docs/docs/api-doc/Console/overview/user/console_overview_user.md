
----------------------------------------------------------------------------------
## console overview users list
* Endpoint: `GET /console/overview/users`
* Purpose: 

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