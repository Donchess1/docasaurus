
## API Documentation {#introduction}
MyBalance provides escrow services to individuals and businesses. This API built for merchants safeguards customers on their platform - allowing customers to initiate, fund, hold and release payments from our escrow vault.

To interact with this API, you need to [create](https://docs.google.com/forms/d/e/1FAIpQLSfVw-lN6ciWaqf6zm-dhHyImK6RltA9KPc91zmZi1TO2gKSCw/viewform) a Merchant account with MyBalance. Your platform API key will be sent via email within 72 hours.

## Core Concepts {#section-1}
This section describes the core concepts in the API.

`Customer`
A customer represents a user account (buyer/seller) on MyBalance which you must create if not already existing in order for a transaction to be initiated successfully.

`Transaction`
This is an escrow transaction which represents an arrangement where MyBalance holds and releases funds for a transaction once specified conditions are met.

`Settlement`
As the name implies, this represents payouts made to the merchant wallet once an escrow transaction has been completed and funds have been released.

`Dispute`
A dispute arises when there is a conflict between the buyer and seller, such as when the buyer decides to reject a delivered item or when seller does not receive funds in their wallet, necessitating resolution.


## Getting Started {#section-2}

# Authentication
All API requests must be authenticated. You must use a valid API Key to send requests to the API endpoints. Each API request requires the following set of headers:

| Header   | Description |
|--------|-----|
| Authorization  | Your Merchant API Key.  |

# Response
This is an highlight of the API response returned for the requests that you make:

|Field	|   Description |
|------|------|
|success    |	Indicates whether the API call was successful. Values can be true for success or false for failure. Success is returned with 2XX status codes, while failure with 4XX status codes.|
|message	|   A human-readable message providing information about the response. If the value is Validation error, more detailed information can be found in errors.|
|data	|Contains the data returned from the API, if any.|
|errors	|Provides information about any errors encountered during POST requests, particularly useful if success value is false and Validation error is returned in the message field.|
|meta	|   Stores additional information about the response, such as pagination details, filters applied, etc.|

# Status Codes

|Error Code    |	Description |
|---|----|
|2XX	|Indicates that the request was successful and action was carried out as expected. Check message for more information.
|4XX	|An error occurred while executing request. 400 status code means it's a bad request. We always include a message parameter in the response which provides a description of the error. If its value is Validation error, check errors for detailed information. 401 implies an Un-authorized request. 404 means the resource requested (endpoint/data) does not exist. 403 means the request is forbidden. 429 means your request was rate-limited.
|5XX	|This indicates an error processing the request from the API, possibly due to server downtime or unavailability. Please contact our support team via mybalance@oinvent.com if you receive this status code.

AUTHORIZATION <div className="opacity-low"> API Key </div>
<div class="no-border-table">
|Key         |       Authorization|
|----------------------|----------------|
|Value       |             •••••••|
</div>