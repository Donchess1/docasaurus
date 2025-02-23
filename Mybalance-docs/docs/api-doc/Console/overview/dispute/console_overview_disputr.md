
----------------------------------------------------------------------------------
## User's General Events
* Endpoint: `GET /console/overview/disputes`
* Purpose: console overview disputes list

```json
Authorization
API Key
```

> Body parameter
```json
{
  
}
```

200_OK Response


```json
[
  {
    "period": "<string>",
    "startDate": "<dateTime>",
    "endDate": "<dateTime>",
    "total": "<integer>",
    "low": {
      "PENDING": {
        "count": "<integer>"
      },
      "PROGRESS": {
        "count": "<integer>"
      },
      "RESOLVED": {
        "count": "<integer>"
      },
      "TOTAL": {
        "count": "<integer>"
      }
    },
    "medium": {
      "PENDING": {
        "count": "<integer>"
      },
      "PROGRESS": {
        "count": "<integer>"
      },
      "RESOLVED": {
        "count": "<integer>"
      },
      "TOTAL": {
        "count": "<integer>"
      }
    },
    "high": {
      "PENDING": {
        "count": "<integer>"
      },
      "PROGRESS": {
        "count": "<integer>"
      },
      "RESOLVED": {
        "count": "<integer>"
      },
      "TOTAL": {
        "count": "<integer>"
      }
    }
  },
  {
    "period": "<string>",
    "startDate": "<dateTime>",
    "endDate": "<dateTime>",
    "total": "<integer>",
    "low": {
      "PENDING": {
        "count": "<integer>"
      },
      "PROGRESS": {
        "count": "<integer>"
      },
      "RESOLVED": {
        "count": "<integer>"
      },
      "TOTAL": {
        "count": "<integer>"
      }
    },
    "medium": {
      "PENDING": {
        "count": "<integer>"
      },
      "PROGRESS": {
        "count": "<integer>"
      },
      "RESOLVED": {
        "count": "<integer>"
      },
      "TOTAL": {
        "count": "<integer>"
      }
    },
    "high": {
      "PENDING": {
        "count": "<integer>"
      },
      "PROGRESS": {
        "count": "<integer>"
      },
      "RESOLVED": {
        "count": "<integer>"
      },
      "TOTAL": {
        "count": "<integer>"
      }
    }
  }
]
```