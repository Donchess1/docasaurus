
----------------------------------------------------------------------------------
## Resets Password
* Endpoint: `POST /console/check-phone-number`
* Purpose: .

> Body parameter

```json
{
  "phone": "59291388180"
}
```
> 200 Response

```json
 {
  "name": "<string>",
  "email": "<email>",
  "id": "<integer>",
  "phone": "49731590135",
  "isVerified": "<boolean>",
  "isBuyer": "<boolean>",
  "isSeller": "<boolean>",
  "isMerchant": "<boolean>",
  "isAdmin": "<boolean>",
  "metadata": "<string>",
  "createdAt": "<dateTime>",
  "updatedAt": "<dateTime>"
}
```
----------------------------------------------------------------------------------