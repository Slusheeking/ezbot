Institutional Activity
get
https://api.unusualwhales.com/api/institution/{name}/activity
The trading activities for a given institution.

Request
Path Parameters
name
string
required
A large entity that manages funds and investments for others. Queryable by name or cik.

Example:
VANGUARD GROUP INC
Query Parameters
date
any
End date to filter institutional reporting data in the format YYYY-MM-DD.Show all...

Example:
2023-03-31
limit
integer
How many items to return. Default: 500. Max: 500. Min: 1.

>= 1
<= 500
Default:
500
Example:
10
page
integer
Page number (use with limit). Starts on page 0.

Example:
1
Responses
200
422
500
Body

application/json

application/json
The trading activities for a given institution.

avg_price
string
Example:
23.49
buy_price
string
Example:
23.49
close
string
The close stock price of the ticker.

Example:
182.91
filing_date
string
An ISO date.

Example:
2024-01-09
price_on_filing
string
The security price on the filing date.

Example:
23.49
price_on_report
string
The security price on the report date.

Example:
23.49
put_call
string
Whether the holding is a put or a call (null if neither).

Example:
put
report_date
string
An ISO date.

Example:
2024-01-09
security_type
string
Example:
Share
sell_price
string
Example:
23.49
shares_outstanding
string
Total outstanding shares for the ticker.

Example:
424295343.0
ticker
string
Example:
MSFT
units
integer
Example:
4103
units_change
integer
The change in units

Example:
-320
Token
:
123
name*
:
string
date
:
date
limit
:
defaults to: 500
page
:
integer
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/institution/{name}/activity \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "avg_price": "432.31",
      "buy_price": null,
      "close": "513.23",
      "filing_date": "2024-12-23",
      "price_on_filing": "510.34",
      "price_on_report": "495.95",
      "put_call": null,
      "report_date": "2024-09-30",
      "security_type": "Fund",
      "sell_price": null,
      "shares_outstanding": "148239423.0",
      "ticker": "SPLG",
      "units": 5000,
      "units_change": -500
    }
  ]
}


Institutional Holdings
get
https://api.unusualwhales.com/api/institution/{name}/holdings
Returns the holdings for a given institution.

Request
Path Parameters
name
string
required
A large entity that manages funds and investments for others. Queryable by name or cik.

Example:
VANGUARD GROUP INC
Query Parameters
date
string
A trading date in the format of YYYY-MM-DD. This is optional and by default the last trading date.

Example:
2024-01-18
end_date
any
A date in the format of YYYY-MM-DD.Show all...

Example:
2023-03-31
limit
integer
How many items to return. Default: 500. Max: 500. Min: 1.

>= 1
<= 500
Default:
500
Example:
10
order
string
Optional columns to order the result by

Allowed values:
date
ticker
security_type
put_call
first_buy
price_first_buy
units
units_change
historical_units
value
avg_price
close
shares_outstanding
Example:
ticker
order_direction
string
Whether to sort descending or ascending. Descending by default.

Allowed values:
desc
asc
Default:
desc
Example:
asc
page
integer
Page number (use with limit). Starts on page 0.

Example:
1
security_types
array[string]
An array of security types

Example:
["Share"]
start_date
any
A date in the format of YYYY-MM-DD.Show all...

Example:
2023-01-01
Responses
200
422
500
Body

application/json

application/json
The holdings for an institution.

avg_price
string
Example:
23.49
close
string
The close stock price of the ticker.

Example:
182.91
date
string
An ISO date.

Example:
2024-01-09
first_buy
string
An ISO date.

Example:
2024-01-09
full_name
string
Example:
MICROSOFT CORP
historical_units
Historical Units
Historical unit counts. Maximum length = 8.

Example:
[4103,4423]
perc_of_share_value
number
The percentage of the total share value of this institution that this holding represents. For example, if the sum of all the institution's holdings total $100 million and this holding has reported value $4 million, then the perc_of_share_value result will be 0.04.

Example:
0.04
perc_of_total
number
The percentage of the total outstanding shares owned by this institution. For example, if there are 500 million outstanding shares and this institution owns 1 million shares, then the perc_of_total result will be 0.002.

Example:
0.002
price_first_buy
string
The close price of the ticker on the first buy date.

Example:
42.39
put_call
string
Whether the holding is a put or a call (null if neither).

Example:
put
sector
string
A financial sector.

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
security_type
string
Example:
Share
shares_outstanding
string
Total outstanding shares for the ticker.

Example:
424295343.0
ticker
string
Example:
MSFT
units
integer
Example:
4103
units_change
integer
The change in units

Example:
-320
value
integer
The rounded total value on the reporting date.

Example:
2429329
Token
:
123
name*
:
string
date
:
string
end_date
:
date
limit
:
defaults to: 500
order
:
Not Setdatetickersecurity_typeput_callfirst_buyprice_first_buyunitsunits_changehistorical_unitsvalueavg_pricecloseshares_outstanding

select an option
order_direction
:
Not Setdescasc

select an option (defaults to: desc)
page
:
integer
security_types
:
array
start_date
:
date
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/institution/{name}/holdings \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "avg_price": "156.53",
      "close": "419.23",
      "date": "2024-10-02",
      "first_buy": "2012-02-23",
      "full_name": "MICROSOFT CORP",
      "historical_units": [
        4103,
        4423
      ],
      "perc_of_share_value": 0.04,
      "perc_of_total": 0.002,
      "price_first_buy": "23.42",
      "put_call": null,
      "sector": "Technology",
      "security_type": "Share",
      "shares_outstanding": "71984388.0",
      "ticker": "MSFT",
      "units": 4103,
      "units_change": -320,
      "value": 1672230
    },
    {
      "avg_price": "359.21",
      "close": "568.23",
      "date": "2024-10-02",
      "first_buy": "2019-12-15",
      "full_name": "ADOBE INC",
      "historical_units": [
        500,
        0
      ],
      "perc_of_share_value": 0.04,
      "perc_of_total": 0.002,
      "price_first_buy": "239.33",
      "put_call": null,
      "sector": "Technology",
      "security_type": "Share",
      "shares_outstanding": "6714388.0",
      "ticker": "ADBE",
      "units": 500,
      "units_change": 500,
      "value": 250000
    }
  ]
}


Sector Exposure
get
https://api.unusualwhales.com/api/institution/{name}/sectors
The sector exposure for a given institution.

Request
Path Parameters
name
string
required
A large entity that manages funds and investments for others. Queryable by name or cik.

Example:
VANGUARD GROUP INC
Query Parameters
date
any
A date in the format of YYYY-MM-DD.Show all...

Example:
2023-03-31
limit
integer
How many items to return. Default: 500. Max: 500. Min: 1.

>= 1
<= 500
Default:
500
Example:
10
Responses
200
422
500
Body

application/json

application/json
The sector exposure for an institution.

positions
integer
Example:
5
positions_closed
integer
Example:
2
positions_decreased
integer
Example:
2
positions_increased
integer
Example:
2
report_date
string
An ISO date.

Example:
2024-01-09
sector
string
A financial sector.

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
value
integer
The rounded total value on the reporting date.

Example:
2429329
Token
:
123
name*
:
string
date
:
date
limit
:
defaults to: 500
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/institution/{name}/sectors \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "positions": 5,
      "positions_closed": 1,
      "positions_decreased": 1,
      "positions_increased": 2,
      "report_date": "2024-09-30",
      "sector": "Technology",
      "value": "1948023952"
    },
    {
      "positions": 7,
      "positions_closed": 4,
      "positions_decreased": 2,
      "positions_increased": 3,
      "report_date": "2024-09-30",
      "sector": "Basic Materials",
      "value": "43952"
    }
  ]
}


List of Institutions
get
https://api.unusualwhales.com/api/institutions
Returns a list of institutions.

Request
Query Parameters
limit
integer
How many items to return. Default: 500. Max: 500. Min: 1.

>= 1
<= 500
Default:
500
Example:
10
max_share_value
string
The max value of the given field.

Example:
10.0
max_total_value
string
The max value of the given field.

Example:
10.0
min_share_value
string
The min value of the given field.

Example:
0.5
min_total_value
string
The min value of the given field.

Example:
0.5
name
string
A large entity that manages funds and investments for others. Queryable by name or cik.

Example:
VANGUARD GROUP INC
order
string
Optional columns to order the result by

Allowed values:
name
call_value
put_value
share_value
call_holdings
put_holdings
share_holdings
total_value
warrant_value
fund_value
pfd_value
debt_value
total_holdings
warrant_holdings
fund_holdings
pfd_holdings
debt_holdings
percent_of_total
date
buy_value
sell_value
Example:
name
order_direction
string
Whether to sort descending or ascending. Descending by default.

Allowed values:
desc
asc
Default:
desc
Example:
asc
page
integer
Page number (use with limit). Starts on page 0.

Example:
1
tags
array[string]
An array of institution tags

Example:
["activist"]
Responses
200
422
500
Body

application/json

application/json
responses
/
200
The summary data for an institution.

buy_value
string
The rounded total buy value in the institution's portfolio.

Example:
2394292.0
call_holdings
string
The number of call units in the institution's portfolio.

Example:
2394292.0
call_value
string
The rounded total call value in the institution's portfolio.

Example:
2394292.0
cik
string
The institution's CIK.

Example:
0000102909
date
string
The end date of the report period in ISO format.

Example:
2024-10-02
debt_holdings
string
The number of debt units in the institution's portfolio.

Example:
2394292.0
debt_value
string
The rounded total debt value in the institution's portfolio.

Example:
2394292.0
description
string
The institution's description.

Example:
Florida-based hedge fund founded in 1977 by Paul Singer. Elliott and Singer himself are famous activists known for acquiring board seats and influencing management, but Elliott has many active arms and runs multiple strategies concurrently like distressed debt, convertible arbitrage, equity long/short, and more.
filing_date
string
The latest filing date in ISO format.

Example:
2024-10-02
founder_img_url
string
The URL to the institution's founder's image.

Example:
https://storage.googleapis.com/uwassets/institution-img/ELLIOTT%20INVESTMENT%20MANAGEMENT%20L.P.%20Paul%20Singer.jpg
fund_holdings
string
The number of fund units in the institution's portfolio.

Example:
2394292.0
fund_value
string
The rounded total fund value in the institution's portfolio.

Example:
2394292.0
is_hedge_fund
boolean
Example:
true
logo_url
string
The URL to the institution's logo.

Example:
https://storage.googleapis.com/uwassets/institution-img/ELLIOTT%20INVESTMENT%20MANAGEMENT%20L.P.%20logo.webp
name
string
The institution's name.

Example:
VANGUARD GROUP INC
people
string
Persons of interest in the institution.

Example:
["Paul Singer"]
pfd_holdings
string
The number of preferred share units in the institution's portfolio.

Example:
2394292.0
pfd_value
string
The rounded total preferred share value in the institution's portfolio.

Example:
2394292.0
put_holdings
string
The number of put units in the institution's portfolio.

Example:
2394292.0
put_value
string
The rounded total put value in the institution's portfolio.

Example:
2394292.0
sell_value
string
The rounded total sell value in the institution's portfolio.

Example:
2394292.0
share_value
string
The rounded total share value in the institution's portfolio.

Example:
2394292.0
short_name
string
The institution's short name.

Example:
Vanguard
tags
Tags
Tags related to the institution.

Example:
["activist","value_investor"]
total_value
string
The rounded total value of the institution's portfolio.

Example:
2394292.0
warrant_holdings
string
The number of warrant units in the institution's portfolio.

Example:
2394292.0
warrant_value
string
The rounded total warrant value in the institution's portfolio.

Example:
2394292.0
website
string
The institution's website.

Example:
https://www.elliottmgmt.com/
Token
:
123
limit
:
defaults to: 500
max_share_value
:
string
max_total_value
:
string
min_share_value
:
string
min_total_value
:
string
name
:
string
order
:
Not Setnamecall_valueput_valueshare_valuecall_holdingsput_holdingsshare_holdingstotal_valuewarrant_valuefund_valuepfd_valuedebt_valuetotal_holdingswarrant_holdingsfund_holdingspfd_holdingsdebt_holdingspercent_of_totaldatebuy_valuesell_value

select an option
order_direction
:
Not Setdescasc

select an option (defaults to: desc)
page
:
integer
tags
:
array
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/institutions \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "buy_value": "359232.0",
      "call_holdings": "359232.0",
      "call_value": "359232.0",
      "cik": "0001791786",
      "date": "2024-12-31",
      "debt_holdings": "359232.0",
      "debt_value": "359232.0",
      "description": "Elliott Management Corporation is an American investment management firm. It is also one of the largest activist funds in the world.",
      "filing_date": "2024-10-01",
      "founder_img_url": "https://storage.googleapis.com/uwassets/institution-img/ELLIOTT%20INVESTMENT%20MANAGEMENT%20L.P.%20Paul%20Singer.jpg",
      "fund_holdings": "359232.0",
      "fund_value": "359232.0",
      "is_hedge_fund": true,
      "logo_url": "https://storage.googleapis.com/uwassets/institution-img/ELLIOTT%20INVESTMENT%20MANAGEMENT%20L.P.%20logo.webp",
      "name": "ELLIOTT INVESTMENT MANAGEMENT L.P.",
      "people": [
        "Paul Singer"
      ],
      "pfd_holdings": "359232.0",
      "pfd_value": "359232.0",
      "put_holdings": "359232.0",
      "put_value": "359232.0",
      "sell_value": "359232.0",
      "share_holdings": "359232.0",
      "share_value": "359232.0",
      "short_name": "Elliott Investment Management",
      "tags": [
        "activist"
      ],
      "total_value": "359232.0",
      "warrant_holdings": "359232.0",
      "warrant_value": "359232.0",
      "website": "https://elliott.com"
    }
  ]
}


Recent Late Reports
get
https://api.unusualwhales.com/api/congress/late-reports
Returns the recent late reports by congress members. If a date is given, will only return recent late reports, which's report date is <= the given input date.

Request
Query Parameters
date
string
A trading date in the format of YYYY-MM-DD. This is optional and by default the last trading date.

Example:
2024-01-18
limit
integer
How many items to return. Default: 100. Max: 200. Min: 1.

>= 1
<= 200
Default:
100
Example:
10
ticker
string or null
Optional ticker symbol to filter results

Example:
IOVA
Responses
200
422
500
Body

application/json

application/json
A senate stock

amounts
string
The reported amount range of the transaction.

Example:
$1,000 - $15,000
filed_at_date
string
The filing date as ISO date.

Example:
2023-12-13
issuer
string
The person who executed the transaction.

Example:
spouse
member_type
string
The type of person who executed the transaction.

Allowed values:
senate
house
other
Example:
house
name
string
The Standardized name of the reporter (if found).

Example:
Stephen Cohen
notes
string
Notes of the filing.

Example:
Subholding Of: Stephens Advantage Account Description: FT UNIT 10479 PFD mutual-fund 32500
reporter
string
The person who reported the transaction (as written in filling).

Example:
Stephen Cohen
ticker
string
The stock ticker.

Example:
AAPL
transaction_date
string
The transaction date as ISO date.

Example:
2023-12-06
txn_type
string
The transaction type.

Allowed values:
Buy
Sell (partial)
Purchase
Sale (Partial)
Receive
Sale (Full)
Sell (PARTIAL)
Sell
Exchange
Example:
Sell
Token
:
123
date
:
string
limit
:
defaults to: 100
ticker
:
string,null
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/congress/late-reports \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "amounts": "$15,001 - $50,000",
      "filed_at_date": "2023-02-13",
      "issuer": "not-disclosed",
      "member_type": "house",
      "name": "Stephen Cohen",
      "notes": "Subholding Of: Stephens Advantage Account Description: FT UNIT 10479 PFD mutual-fund 32500",
      "reporter": "Stephen C.",
      "ticker": "FHWVOX",
      "transaction_date": "2023-02-06",
      "txn_type": "Buy"
    },
    {
      "amounts": "$1,000 - $15,000",
      "filed_at_date": "2023-02-13",
      "issuer": "joint",
      "member_type": "house",
      "name": "Deborah Ross",
      "notes": "Subholding Of: Fidelity Brokerage Account stock 8000",
      "reporter": "Debby Ross",
      "ticker": "MSFT",
      "transaction_date": "2023-02-01",
      "txn_type": "Sell"
    }
  ]
}


