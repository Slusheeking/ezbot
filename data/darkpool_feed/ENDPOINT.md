ecent Darkpool Trades
get
https://api.unusualwhales.com/api/darkpool/recent
Returns the latest darkpool trades.

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
max_premium
integer
The maximum premium requested trades should have.

Example:
150000
max_size
integer
The maximum size requested trades should have. Must be a positive integer.

Example:
150000
max_volume
integer
The maximum consolidated volume requested trades should have. Must be a positive integer.

Example:
150000
min_premium
integer
The minimum premium requested trades should have.

>= 0
Default:
0
Example:
50000
min_size
integer
The minimum size requested trades should have. Must be a positive integer.

>= 0
Default:
0
Example:
50000
min_volume
integer
The minimum consolidated volume requested trades should have. Must be a positive integer.

>= 0
Default:
0
Example:
50000
Responses
200
422
500
Body

application/json

application/json
A darkpool trade.

canceled
boolean
Whether the trade has been cancelled.

Example:
true
executed_at
string
The time with timezone when a trade was executed.

Example:
2023-02-16T00:59:44Z
ext_hour_sold_codes
string
The code describing why the trade happened outside of regular market hours. Null if none applies.

Allowed values:
sold_out_of_sequence
extended_hours_trade_late_or_out_of_sequence
extended_hours_trade
Example:
sold_out_of_sequence
market_center
string
The market center code.

Example:
L
nbbo_ask
any
nbbo_ask_quantity
any
nbbo_bid
any
nbbo_bid_quantity
any
premium
string
The total option premium.

Example:
27723806.00
price
string
The price of the trade.

Example:
18.9904
sale_cond_codes
string
The sale condition code. Null if none applies.

Allowed values:
contingent_trade
odd_lot_execution
prior_reference_price
average_price_trade
Example:
contingent_trade
size
integer
The size of the transaction.

Example:
6400
ticker
string
The stock ticker.

Example:
AAPL
tracking_id
integer
The tracking ID of the trade.

Example:
71984388012245
trade_code
string
The trade code. Null if none applies.

Allowed values:
derivative_priced
qualified_contingent_trade
intermarket_sweep
Example:
derivative_priced
trade_settlement
string
The kind of trade settlement.

Allowed values:
cash
next_day
seller
regular
Example:
cash_settlement
volume
integer
The volume of the ticker for the trading day.

Example:
23132119
Token
:
123
date
:
string
limit
:
defaults to: 100
max_premium
:
integer
max_size
:
integer
max_volume
:
integer
min_premium
:
defaults to: 0
min_size
:
defaults to: 0
min_volume
:
defaults to: 0
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/darkpool/recent \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "canceled": false,
      "executed_at": "2023-02-16T00:59:44Z",
      "ext_hour_sold_codes": "extended_hours_trade",
      "market_center": "L",
      "nbbo_ask": "19",
      "nbbo_ask_quantity": 6600,
      "nbbo_bid": "18.99",
      "nbbo_bid_quantity": 29100,
      "premium": "121538.56",
      "price": "18.9904",
      "sale_cond_codes": null,
      "size": 6400,
      "ticker": "QID",
      "tracking_id": 71984388012245,
      "trade_code": null,
      "trade_settlement": "regular_settlement",
      "volume": 9946819
    },
    {
      "canceled": false,
      "executed_at": "2023-02-16T00:59:44Z",
      "ext_hour_sold_codes": "extended_hours_trade",
      "market_center": "L",
      "nbbo_ask": "19",
      "nbbo_ask_quantity": 6600,
      "nbbo_bid": "18.99",
      "nbbo_bid_quantity": 29100,
      "premium": "353214",
      "price": "18.99",
      "sale_cond_codes": null,
      "size": 18600,
      "ticker": "QID",
      "tracking_id": 71984384768588,
      "trade_code": null,
      "trade_settlement": "regular_settlement",
      "volume": 9940419
    }
  ]
}