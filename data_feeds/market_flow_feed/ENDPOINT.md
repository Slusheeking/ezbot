Market Tide
get
https://api.unusualwhales.com/api/market/market-tide
Market Tide is a proprietary tool that can be viewed from the Market Overview page. The Market Tide chart provides real time data based on a proprietary formula that examines market wide options activity and filters out 'noise'.

Date must be the current or a past date. If no date is given, returns data for the current/last market day.

Per default data are returned in 1 minute intervals. Use interval_5m=true to have this return data in 5 minute intervals instead.

For example:

$15,000 in calls transacted at the ask has the effect of increasing the daily net call premium by $15,000.
$10,000 in calls transacted at the bid has the effect of decreasing the daily net call premium by $10,000.
The resulting net premium from both of these trades would be $5000 (+ $15,000 - $10,000).

Transactions taking place at the mid are not accounted for.

In theory:

The sentiment in the options market becomes increasingly bullish if:

The aggregated CALL PREMIUM is increasing at a faster rate.
The aggregated PUT PREMIUM is decreasing at a faster rate.
The sentiment in the options market becomes increasingly bearish if:

The aggregated CALL PREMIUM is decreasing at a faster rate.
The aggregated PUT PREMIUM is increasing at a faster rate.
This can be used to build a market overview such as:

market tide
Data goes back to 2022-09-28

Request
Query Parameters
date
string
A trading date in the format of YYYY-MM-DD. This is optional and by default the last trading date.

Example:
2024-01-18
interval_5m
boolean
Return data in 5 minutes intervals.

Default:
true
Example:
false
otm_only
boolean
Only include out of the money transactions.

Default:
false
Example:
true
Responses
200
422
500
Body

application/json

application/json
net_call_premium
string
Defined as (call premium ask side) - (call premium bid side).

Example:
-29138464
net_put_premium
string
Defined as (put premium ask side) - (put premium bid side).

Example:
23924325
net_volume
integer
Defined as (call volume ask side) - (call volume bid side) - ((put volume ask side) - (put volume bid side)).

Example:
64312
timestamp
string
The start time of the tick as a timestamp with timezone.

Example:
2023-09-07T09:30:00-04:00
Token
:
123
date
:
string
interval_5m
:
Not SetFalseTrue

select an option (defaults to: true)
otm_only
:
Not SetFalseTrue

select an option (defaults to: false)
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/market/market-tide \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "date": "2023-09-08",
      "net_call_premium": "660338.0000",
      "net_put_premium": "-547564.0000",
      "net_volume": 23558,
      "timestamp": "2023-09-08T09:30:00-04:00"
    },
    {
      "date": "2023-09-08",
      "net_call_premium": "4907138.0000",
      "net_put_premium": "-1709539.0000",
      "net_volume": 64312,
      "timestamp": "2023-09-08T09:31:00-04:00"
    },
    {
      "date": "2023-09-08",
      "net_call_premium": "4839265.0000",
      "net_put_premium": "-2731793.0000",
      "net_volume": 80029,
      "timestamp": "2023-09-08T09:32:00-04:00"
    }
  ]
}