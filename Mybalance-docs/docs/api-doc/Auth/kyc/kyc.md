
----------------------------------------------------------------------------------
## Update KYC

* Endpoint: `PUT /v1/auth/kyc`
* Purpose: Update KYC


## Authorization
```json
API key
```

> Body parameter
```json
{
  "kycType": "BVN",
  "kycMetaId": "<uuid>"
}
```
> 200 Response
```json
{
  "kycType": "BVN",
  "kycMetaId": "<uuid>"
}
```
----------------------------------------------------------------------------------