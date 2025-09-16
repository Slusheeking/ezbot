Analyst Rating
get
https://api.unusualwhales.com/api/screener/analysts
Returns the latest analyst rating for the given ticker.

Request
Query Parameters
action
string
The action of the recommendation.

Allowed values:
initiated
reiterated
downgraded
upgraded
maintained
Example:
maintained
limit
integer
How many items to return. Default: 500, Max: 500, Min: 1

Examples:
100
recommendation
string
The recommendation the analyst gave out.

Allowed values:
buy
hold
sell
Example:
hold
ticker
string
A single ticker

Example:
AAPL
Responses
200
422
500
Analyst rating response

Body

application/json

application/json
A rating of an analyst.

action
string
The action of the recommendation.

Allowed values:
initiated
reiterated
downgraded
upgraded
maintained
target raised
target lowered
Example:
maintained
analyst_name
string
The name of the analyst.

Example:
David Vogt
firm
string
The firm the analyst is working for.

Example:
UBS
recommendation
string
The recommendation the analyst gave out.

Allowed values:
buy
hold
sell
Example:
hold
sector
string
The financial sector of the ticker. Empty if unknown or not applicable such as ETF/Index.

Allowed values:
Basic Materials
Communication Services
Consumer Cyclical
Consumer Defensive
Energy
Financial Services
Healthcare
Industrials
Real Estate
Technology
Utilities
Example:
Technology
target
string
The target price of the rating.

Example:
190.0
ticker
any
A financial sector.

timestamp
string
The UTC timestamp, when the rating was released.

Example:
2023-09-08T12:21:10Z
Token
:
123
action
:
Not Setinitiatedreiterateddowngradedupgradedmaintained

select an option
limit
:
example: 100
recommendation
:
Not Setbuyholdsell

select an option
ticker
:
string
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/screener/analysts \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "action": "maintained",
      "analyst_name": "Tyler Radke",
      "firm": "Citi",
      "recommendation": "buy",
      "sector": "Technology",
      "target": "420.0",
      "ticker": "MSFT",
      "timestamp": "2023-09-11T11:21:12Z"
    },
    {
      "action": "maintained",
      "analyst_name": "Mark Rothschild",
      "firm": "Canaccord Genuity",
      "recommendation": "hold",
      "sector": "Conglomerates",
      "target": "11.75",
      "ticker": "DRETF",
      "timestamp": "2023-09-11T11:11:32Z"
    }
  ]
}