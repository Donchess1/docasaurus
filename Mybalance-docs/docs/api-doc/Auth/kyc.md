
----------------------------------------------------------------------------------
## Update KYC

* Endpoint: `PUT /v1/auth/kyc`
* Purpose: Update KYC
* To perform this operation, you must be authenticated by jwtAuth
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