
----------------------------------------------------------------------------------
## console overview transactions list
* Endpoint: `GET /console/overview/transactions`
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
    "currency": "<string>",
    "deposits": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FAILED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "CANCELLED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    },
    "withdrawals": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FAILED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    },
    "escrows": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "REJECTED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FUFILLED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "REVOKED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    },
    "settlements": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FAILED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    },
    "merchantSettlements": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FAILED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    },
    "productSettlements": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FAILED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    },
    "productPurchases": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FAILED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    }
  },
  {
    "period": "<string>",
    "startDate": "<dateTime>",
    "endDate": "<dateTime>",
    "total": "<integer>",
    "currency": "<string>",
    "deposits": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FAILED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "CANCELLED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    },
    "withdrawals": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FAILED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    },
    "escrows": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "REJECTED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FUFILLED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "REVOKED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    },
    "settlements": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FAILED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    },
    "merchantSettlements": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FAILED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    },
    "productSettlements": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FAILED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    },
    "productPurchases": {
      "PENDING": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "SUCCESSFUL": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "FAILED": {
        "volume": "<number>",
        "count": "<integer>"
      },
      "TOTAL": {
        "volume": "<number>",
        "count": "<integer>"
      }
    }
  }
]

```
----------------------------------------------------------------------------------