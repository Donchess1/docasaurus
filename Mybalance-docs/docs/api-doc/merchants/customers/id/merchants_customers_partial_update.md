
----------------------------------------------------------------------------------
## 
* Endpoint: `PATCH /merchants/customers/:id`
* Purpose:

##Authorization

```json
API Key
```

##Query Params
```json
id              <string> (Required)
```

> Body parameter

```json
{
  "firstName": "<string>",
  "lastName": "<string>",
  "phoneNumber": "50157552691"
}
```
> 200 Response

```json
 {
  "firstName": "<string>",
  "lastName": "<string>",
  "phoneNumber": "50157552691"
}
```
----------------------------------------------------------------------------------