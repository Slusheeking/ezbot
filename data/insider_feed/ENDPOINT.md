Transactions
get
https://api.unusualwhales.com/api/insider/transactions
Returns the latest insider transactions.

By default all transacations that have been filled by the same person on the same day with the same trade code are aggregated into a single row. Each of those aggregated rows will a field trade_ids which contains the ids of the single transactions that were aggregated as well as the amount of transactions that were aggregated.

If you want to disable this behaviour you can set the group parameter to false to receive the single transacations as they have been filled.

Request
Query Parameters
common_stock_only
boolean
Only include common stock transactions

Examples:
true
industries
string
Filter by company industry or industries

Examples:
Airlines
is_director
boolean
Filter transactions by company directors

Examples:
true
is_officer
boolean
Filter transactions by company officers

Examples:
true
is_s_p_500
boolean
Only include S&P 500 companies

Examples:
true
is_ten_percent_owner
boolean
Filter transactions by 10% owners

Examples:
false
limit
integer
How many items to return. Default: 500. Max: 500. Min: 1.

>= 1
<= 500
Default:
500
Example:
10
market_cap_size
string
Size category of company market cap (small, mid, large)

Examples:
large
max_amount
string
Maximum number of shares in transaction

Examples:
10000
max_earnings_dte
string
Maximum days to earnings

Examples:
30
max_marketcap
integer
The maximum marketcap. Min: 0.

>= 0
Example:
250000000
max_price
string
Maximum stock price at the time of transaction

Examples:
50.75
max_value
string
Maximum transaction value in dollars

Examples:
1000000
min_amount
string
Minimum number of shares in transaction

Examples:
1000
min_earnings_dte
string
Minimum days to earnings (filter for companies reporting soon)

Examples:
5
min_marketcap
integer
The minimum marketcap. Min: 0.

>= 0
Example:
1000000
min_price
string
Minimum stock price at the time of transaction

Examples:
10.5
min_value
string
Minimum transaction value in dollars

Examples:
100000
owner_name
string
Name of the insider who made the transaction

Examples:
John Doe
page
integer
Page number (use with limit). Starts on page 0.

Example:
1
sectors
string
Filter by company sector(s)

Examples:
Healthcare
security_ad_codes
string
Filter by security acquisition disposition codes

Examples:
["COM","PRF"]
ticker_symbol
string
A comma separated list of tickers. To exclude certain tickers prefix the first ticker with a -.

Example:
AAPL,INTC
transaction_codes[]
string
Filter by transaction codes (P=Purchase, S=Sale, etc.)

Examples:
["P","S"]
Responses
200
Body

application/json

application/json
responses
/
200
An aggregated insider trade

amount
integer
The amount of the insider trade.

Example:
1000
date_excercisable
string
The date excercisable of the insider trade.

Example:
2023-12-06
director_indirect
string
The director indirect of the insider trade.

Example:
John Doe
expiration_date
string
The expiration date of the insider trade.

Example:
2023-12-06
filing_date
string
The filing date of the insider trade.

Example:
2023-12-06
formtype
string
The form type of the insider trade.

Example:
4
ids
Insider IDs
The IDs of the insider trade.

Example:
["1234"]
is_10b5_1
boolean
True if this insider trade was part of a 10b5-1 plan

Example:
true
is_director
boolean
Whether the insider is a director.

Example:
true
is_officer
boolean
Whether the insider is an officer.

Example:
true
is_ten_percent_owner
boolean
Whether the insider is a 10% owner.

Example:
true
natureofownership
string
The nature of ownership of the insider trade.

Example:
Direct
officer_title
string
The officer title of the insider trade.

Example:
CEO
owner_name
string
The owner name of the insider trade.

Example:
John Doe
price
string
The price of the insider trade.

Example:
123.45
price_excercisable
string
The price excercisable of the insider trade.

Example:
123.45
security_ad_code
string
The security AD code of the insider trade.

Example:
1234
security_title
string
The security title of the insider trade.

Example:
Common Stock
shares_owned_after
integer
The number of shares owned after the insider trade.

Example:
2000
shares_owned_before
integer
The number of shares owned before the insider trade.

Example:
1000
ticker
string
The stock ticker.

Example:
AAPL
transaction_code
string
The transaction code of the insider trade.

Example:
S
transaction_date
string
The transaction date of the insider trade.

Example:
2023-12-06
transactions
integer
The number of transactions of the insider trade.

Example:
1
Token
:
123
common_stock_only
:
Not SetFalseTrue

select an option
industries
:
example: Airlines
is_director
:
Not SetFalseTrue

select an option
is_officer
:
Not SetFalseTrue

select an option
is_s_p_500
:
Not SetFalseTrue

select an option
is_ten_percent_owner
:
Not SetFalseTrue

select an option
limit
:
defaults to: 500
market_cap_size
:
example: large
max_amount
:
example: 10000
max_earnings_dte
:
example: 30
max_marketcap
:
integer
max_price
:
example: 50.75
max_value
:
example: 1000000
min_amount
:
example: 1000
min_earnings_dte
:
example: 5
min_marketcap
:
integer
min_price
:
example: 10.5
min_value
:
example: 100000
owner_name
:
example: John Doe
page
:
integer
sectors
:
example: Healthcare
security_ad_codes
:
example: ["COM","PRF"]
ticker_symbol
:
string
transaction_codes[]
:
example: ["P","S"]


Sector Flow
get
https://api.unusualwhales.com/api/insider/{sector}/sector-flow
Returns an aggregated view of the insider flow for the given sector.

This can be used to quickly examine the buy & sell insider flow for a given trading date

Request
Path Parameters
sector
string
required
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
Responses
200
Body

application/json

application/json
The total buy/sell insider flow for a given sector on a given date. If there have been buy & sells on the same day then there will be 2 rows for that day.

avg_price
string
The average price of the insider trade.

Example:
123.45
buy_sell
string
Whether the insider bought or sold.

Allowed values:
buy
sell
Example:
buy
date
string
A trading date in ISO format.

Example:
2023-09-08
premium
string
The premium of the insider trade.

Example:
123.45
transactions
integer
The number of transactions of the insider trade.

Example:
1
uniq_insiders
integer
The number of unique insiders of the insider trade.

Example:
1
volume
integer
The volume of the insider trade.

Example:
1000
Token
:
123
sector*
:
Basic MaterialsCommunication ServicesConsumer CyclicalConsumer DefensiveEnergyFinancial ServicesHealthcareIndustrialsReal EstateTechnologyUtilities

Basic Materials
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/insider/Basic%20Materials/sector-flow \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "avg_price": 162.32,
      "buy_sell": "sell",
      "date": "2024-12-12",
      "premium": "664386",
      "transactions": 54,
      "uniq_insiders": 10,
      "volume": 244331
    }
  ]
}

