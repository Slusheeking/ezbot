Flow Alerts
get
https://api.unusualwhales.com/api/option-trades/flow-alerts
Returns the latest flow alerts.

Request
Query Parameters
all_opening
boolean
Boolean flag whether all transactions are opening transactions based on OI, Size & Volume.

Default:
true
Example:
true
is_ask_side
boolean
Boolean flag whether a transaction is ask side.

Default:
true
Example:
true
is_bid_side
boolean
Boolean flag whether a transaction is bid side.

Default:
true
Example:
true
is_call
boolean
Boolean flag whether a transaction is a call.

Default:
true
Example:
true
is_floor
boolean
Boolean flag whether a transaction is from the floor.

Default:
true
Example:
true
is_otm
boolean
Only include contracts which are currently out of the money.

Example:
true
is_put
boolean
Boolean flag whether a transaction is a put.

Default:
true
Example:
true
is_sweep
boolean
Boolean flag whether a transaction is a intermarket sweep.

Default:
true
Example:
true
issue_types[]
array[string]
An array of 1 or more issue types.

Allowed values:
Common Stock
ETF
Index
ADR
Example:
["Common Stock","Index"]
limit
integer
How many items to return. Default: 100. Max: 200. Min: 1.

>= 1
<= 200
Default:
100
Example:
10
max_diff
string
The minimum OTM diff of a contract. Given a strike price of 120 and an underlying price of 98 the diff for a call option would equal to: (120 - 98) / 98 = 0.2245Show all...

Example:
0.53
max_dte
integer
The maximum days to expiry. Min: 0.

>= 0
Example:
3
max_open_interest
integer
The maximum open interest on that alert's contract at the time of the alert. Min: 0.

>= 0
Example:
125
max_premium
integer
The maximum premium on that alert. Min: 0.

>= 0
Example:
12500.5
max_size
integer
The maximum size on that alert. Min: 0.

>= 0
Example:
125
max_volume
integer
The maximum volume on that alert's contract at the time of the alert. Min: 0.

>= 0
Example:
125
max_volume_oi_ratio
integer
The maximum ratio of contract volume to contract open interest. If the open interest of a contract is zero, then this ratio is evaluated as if the open interest of the contract was one (to avoid divide by zero errors). For example, if you set this ratio to 50, then a contract with zero open interest and 75 volume will NOT be included in your results.

>= 0
Example:
1.58
min_diff
string
The minimum OTM diff of a contract. Given a strike price of 120 and an underlying price of 98 the diff for a call option would equal to: (120 - 98) / 98 = 0.2245Show all...

Example:
0.53
min_dte
integer
The minimum days to expiry. Min: 0.

>= 0
Example:
1
min_open_interest
integer
The minimum open interest on that alert's contract at the time of the alert. Min: 0.

>= 0
Example:
125
min_premium
integer
The minimum premium on that alert. Min: 0.

>= 0
Example:
12500.5
min_size
integer
The minimum size on that alert. Size is defined as the sum of the sizes of all transactions that make up the alert. Min: 0.

>= 0
Example:
125
min_volume
integer
The minimum volume on that alert's contract at the time of the alert. Min: 0.

>= 0
Example:
125
min_volume_oi_ratio
integer
The minimum ratio of contract volume to contract open interest. If the open interest of a contract is zero, then this ratio is evaluated as if the open interest of the contract was one (to avoid divide by zero errors). For example, if you set this ratio to 10, then a contract with zero open interest and 7 volume will NOT be included in your results.

>= 0
Example:
0.32
newer_than
string
The unix time in milliseconds or seconds at which no older results will be returned. Can be used with older_than to paginate by time. Also accepts an ISO date (example: 2024-01-25).

Example:
1_715_083_417
older_than
string
The unix time in milliseconds or seconds at which no newer results will be returned. Can be used with newer_than to paginate by time. Also accepts an ISO date (example: 2024-01-25).

Example:
1_715_083_417
rule_name[]
array[string]
An array of 1 or more rule name.

Allowed values:
FloorTradeSmallCap
FloorTradeMidCap
RepeatedHits
RepeatedHitsAscendingFill
RepeatedHitsDescendingFill
FloorTradeLargeCap
OtmEarningsFloor
LowHistoricVolumeFloor
SweepsFollowedByFloor
Example:
["RepeatedHits","RepeatedHitsAscendingFill"]
ticker_symbol
string
A comma separated list of tickers. To exclude certain tickers prefix the first ticker with a -.

Example:
AAPL,INTC
Responses
200
422
500
Body

application/json

application/json
Representation of a flow alert.

alert_rule
string
The name of the alert rule.

Example:
RepeatedHits
all_opening_trades
boolean
Example:
false
created_at
string
A UTC timestamp.

Example:
2023-12-12T16:35:52.168490Z
expiry
string
The contract expiry date in ISO format.

Example:
2023-12-22
expiry_count
integer
The amount of expiries belonging to the trade. This is only greater than 1 if it is a multileg trade.

Example:
2
has_floor
boolean
Example:
false
has_multileg
boolean
Whether the trade is a multileg trade.

Example:
false
has_singleleg
boolean
Whether the trade is a singleleg trade.

Example:
true
has_sweep
boolean
Whether the trade is a sweep.

Example:
true
open_interest
any
option_chain
string
The option symbol of the contract.Show all...

price
any
strike
string
The contract strike.

Example:
375
ticker
any
total_ask_side_prem
any
total_bid_side_prem
any
total_premium
any
total_size
any
trade_count
any
type
string
The contract type.

Allowed values:
call
put
Example:
call
underlying_price
any
volume
any
volume_oi_ratio
any
Token
:
123
all_opening
:
Not SetFalseTrue

select an option (defaults to: true)
is_ask_side
:
Not SetFalseTrue

select an option (defaults to: true)
is_bid_side
:
Not SetFalseTrue

select an option (defaults to: true)
is_call
:
Not SetFalseTrue

select an option (defaults to: true)
is_floor
:
Not SetFalseTrue

select an option (defaults to: true)
is_otm
:
Not SetFalseTrue

select an option
is_put
:
Not SetFalseTrue

select an option (defaults to: true)
is_sweep
:
Not SetFalseTrue

select an option (defaults to: true)
issue_types[]
:
array
limit
:
defaults to: 100
max_diff
:
string
max_dte
:
integer
max_open_interest
:
integer
max_premium
:
integer
max_size
:
integer
max_volume
:
integer
max_volume_oi_ratio
:
integer
min_diff
:
string
min_dte
:
integer
min_open_interest
:
integer
min_premium
:
integer
min_size
:
integer
min_volume
:
integer
min_volume_oi_ratio
:
integer
newer_than
:
string
older_than
:
string
rule_name[]
:
array
ticker_symbol
:
string
