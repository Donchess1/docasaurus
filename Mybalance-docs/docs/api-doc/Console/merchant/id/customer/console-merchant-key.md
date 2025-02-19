
----------------------------------------------------------------------------------
## User's General Events
* Endpoint: `GET /console/merchants/:id/customers?search=<string>&ordering=<string>&page=<integer>&size=<integer>`
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
      "id": "<integer>",
      "userType": "<string>",
      "userId": "<string>",
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>",
      "fullName": "<string>",
      "phoneNumber": "<string>",
      "email": "<string>",
      "wallets": "<string>",
      "systemMetrics": "<string>"
    },
    {
      "id": "<integer>",
      "userType": "<string>",
      "userId": "<string>",
      "createdAt": "<dateTime>",
      "updatedAt": "<dateTime>",
      "fullName": "<string>",
      "phoneNumber": "<string>",
      "email": "<string>",
      "wallets": "<string>",
      "systemMetrics": "<string>"
    }
  ],
  "next": "<uri>",
  "previous": "<uri>"

}
```
----------------------------------------------------------------------------------