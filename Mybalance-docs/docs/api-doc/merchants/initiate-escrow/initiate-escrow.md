
----------------------------------------------------------------------------------
## merchants initiate-escrow create
* Endpoint: `POST v1/merchants/initiate-escrow`
* Purpose: 

## Authorization

```json
Bearer Token
```

> Body parameter
```json
{
    "buyer": "khristo09@gmail.com",
    "redirectUrl": "https://tiny.com",
    "entities": [
        {
            "seller": "stepabod@yahoo.com",
            "items": [
                {
                    "title": "DOC",
                    "description": "Chicken",
                    "category": "GOODS",
                    "itemQuantity": "15",
                    "deliveryDate": "2025-02-5",
                    "amount": "4594"
                }
            ]
        }
    ],
    "currency": "NGN"
}
```

> 200 Response

```json
{
  "buyer": "<email>",
  "redirectUrl": "<uri>",
  "entities": [
    {
      "seller": "<email>",
      "items": [
        {
          "title": "<string>",
          "description": "<string>",
          "category": "GOODS",
          "itemQuantity": "<integer>",
          "deliveryDate": "<date>",
          "amount": "<integer>"
        },
        {
          "title": "<string>",
          "description": "<string>",
          "category": "GOODS",
          "itemQuantity": "<integer>",
          "deliveryDate": "<date>",
          "amount": "<integer>"
        }
      ]
    },
    {
      "seller": "<email>",
      "items": [
        {
          "title": "<string>",
          "description": "<string>",
          "category": "GOODS",
          "itemQuantity": "<integer>",
          "deliveryDate": "<date>",
          "amount": "<integer>"
        },
        {
          "title": "<string>",
          "description": "<string>",
          "category": "GOODS",
          "itemQuantity": "<integer>",
          "deliveryDate": "<date>",
          "amount": "<integer>"
        }
      ]
    }
  ],
  "payoutConfiguration": "<uuid>",
  "currency": "NGN"
}
```
-----------------------------------------------------------------------------