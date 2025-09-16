Hottest Chains
get
https://api.unusualwhales.com/api/screener/option-contracts
A contract screener endpoint to screen the market for contracts by a variety of filter options.

For an example of what can be build with this endpoint check out the Hottest Contracts on UnusualWhales.

NOTE: Contracts with a volume of less than 200 are not being returned

Request
Query Parameters
date
string
A trading date in the format of YYYY-MM-DD. This is optional and by default the last trading date.

Example:
2024-01-18
exclude_ex_div_ticker
boolean
When set to true, all tickers that trade ex-dividend today will be excluded. This is useful since on the day prior to the ex-dividend date, there will be above-average ITM call flow due to dividend arbitrage traders.

expiry_dates[]
array[string]
An array of 1 or more expiry dates.

Example:
["2024-02-02","2024-01-26"]
is_otm
boolean
Only include contracts which are currently out of the money.

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
How many items to return. Default: 50. Max: 250. Min: 1.

>= 1
<= 250
Default:
1
Example:
10
max_ask_perc
string
The maximum ask percentage of volume that transacted on the ask.

Examples:
0.45
max_ask_side_perc_7_day
string
The maximum percentage of days over the last 7 days where the contract traded primarily on the ask side

Examples:
0.45
max_avg_price
string
The maximum average price of the contract.

Examples:
25.00
max_bear_perc
string
The maximum bear percentage.

Examples:
0.45
max_bid_perc
string
The maximum bid percentage of volume that transacted on the bid.

Examples:
0.45
max_bid_side_perc_7_day
string
The maximum percentage of days over the last 7 days where the contract traded primarily on the bid side

Examples:
0.45
max_bull_perc
string
The maximum bull percentage.

Examples:
0.45
max_close
string
The maximum contract price (not underlying price).

Examples:
25.00
max_daily_perc_change
string
The maximum intraday price change for the contract since market open.

Examples:
0.6
max_days_of_oi_increases
integer
The maximum days of consecutive trading days where the open interest increased

Examples:
10
max_days_of_vol_greater_than_oi
integer
The maximum days of consecutive days where volume was greater than open interest.

Examples:
7
max_delta
string
The maximum delta. Acceptable range: -1.00 to +1.00.

Examples:
0.80
max_diff
string
The maximum OTM diff of a contract.

Examples:
1.34
max_dte
integer
The maximum days to expiry.

Examples:
3
max_earnings_dte
integer
The maximum days to earnings.

Examples:
30
max_floor_volume
integer
The maximum floor volume on that contract.

Examples:
55800
max_floor_volume_ratio
string
The maximum floor volume to contract volume ratio.

Examples:
0.45
max_from_high_perc
string
The maximum percentage change of the current price from todays high. Acceptable range: -1.00 to +inf.

Examples:
0.45
max_from_low_perc
string
The maximum percentage change of the current price from todays low. Acceptable range: -1.00 to +inf.

Examples:
0.45
max_gamma
string
The maximum gamma. Acceptable range: 0.00 to +inf.

Examples:
0.15
max_iv_perc
string
The maximum implied volatility percentage.

Examples:
0.45
max_marketcap
string
The maximum marketcap.

Examples:
250000000
max_multileg_volume_ratio
string
The maximum multi leg volume to contract volume ratio.

Examples:
0.5
max_oi_change
integer
The maximum open interest change as an absolute change.

Examples:
5000
max_oi_change_perc
string
The maximum open interest change percentage. Acceptable range: -1.00 to +inf.

Examples:
0.50
max_open_interest
integer
The maximum open interest on that contract.

Examples:
55600
max_perc_change
string
The maximum % price change of the contract to the previous day. Acceptable range: -1.00 to +inf.

Examples:
0.68
max_premium
string
The maximum premium on that contract.

Examples:
53100.32
max_return_on_capital_perc
string
The maximum return on capital percentage (ROC).

Examples:
0.45
max_skew_perc
string
The maximum skew percentage.Setting this to 0.8 would return all contracts where max 80% of vol transacted on the ask or bid side

Examples:
0.45
max_strike
string
The maximum strike.

Examples:
1200
max_sweep_volume_ratio
string
The maximum sweep volume ratio. Acceptable range: 0.00 to 1.00.

Examples:
0.75
max_theta
string
The maximum theta. Acceptable range: -inf to 0.00.

Examples:
-0.01
max_transactions
integer
The maximum number of transactions.

Examples:
500
max_underlying_price
string
The maximum stock price.

Examples:
10.53
max_vega
string
The maximum vega. Acceptable range: 0.00 to +inf.

Examples:
0.25
max_volume
integer
The maximum volume on that contract.

Examples:
55600
max_volume_oi_ratio
string
The maximum contract volume to open interest ratio.

Examples:
1.58
max_volume_ticker_vol_ratio
string
The maximum ratio of contract volume to total option volume of the underlying. Acceptable range: 0.00 to 1.00.

Examples:
0.85
min_ask_perc
string
The minimum ask percentage of volume that transacted on the ask.

Examples:
0.19
min_ask_side_perc_7_day
string
The minimum percentage of days over the last 7 days where the contract traded primarily on the ask side

Examples:
0.19
min_avg_price
string
The minimum average price of the contract.

Examples:
1.50
min_bear_perc
string
The minimum bear percentage.

Examples:
0.19
min_bid_perc
string
The minimum bid percentage of volume that transacted on the bid.

Examples:
0.19
min_bid_side_perc_7_day
string
The minimum percentage of days over the last 7 days where the contract traded primarily on the bid side

Examples:
0.19
min_bull_perc
string
The minimum bull percentage.

Examples:
0.19
min_close
string
The minimum contract price (not underlying price).

Examples:
1.50
min_daily_perc_change
string
The minimum intraday price change of the contract from open till now.

Examples:
0.2
min_days_of_oi_increases
integer
The minimum days of consecutive trading days where the open interest increased

Examples:
3
min_days_of_vol_greater_than_oi
integer
The minimum days of consecutive days where volume was greater than open interest.

Examples:
2
min_delta
string
The minimum delta. Acceptable range: -1.00 to +1.00.

Examples:
-0.50
min_diff
string
The minimum OTM diff of a contract.

Examples:
0.53
min_dte
integer
The minimum days to expiry.

Examples:
1
min_earnings_dte
integer
The minimum days to earnings.

Examples:
1
min_floor_volume
integer
The minimum floor volume on that contract.

Examples:
12300
min_floor_volume_ratio
string
The minimum floor volume to contract volume ratio.

Examples:
0.2
min_from_high_perc
string
The minimum percentage change of the current price from todays high. Acceptable range: -1.00 to +inf.

Examples:
0.19
min_from_low_perc
string
The minimum percentage change of the current price from todays low. Acceptable range: -1.00 to +inf.

Examples:
0.19
min_gamma
string
The minimum gamma. Acceptable range: 0.00 to +inf.

Examples:
0.01
min_iv_perc
string
The minimum implied volatility percentage.

Examples:
0.19
min_marketcap
string
The minimum marketcap.

Examples:
1000000
min_multileg_volume_ratio
string
The minimum multi leg volume to contract volume ratio.

Examples:
0.3
min_oi_change
integer
The minimum open interest change as an absolute change.

Examples:
-1000
min_oi_change_perc
string
The minimum open interest change percentage. Acceptable range: -1.00 to +inf.

Examples:
-0.25
min_open_interest
integer
The minimum open interest on that contract.

Examples:
12300
min_perc_change
string
The minimum % price change of the contract to the previous day. Acceptable range: -1.00 to +inf.

Examples:
0.5
min_premium
string
The minimum premium on that contract.

Examples:
12500.5
min_return_on_capital_perc
string
The minimum return on capital percentage (ROC).

Examples:
0.19
min_skew_perc
string
The minimum skew percentage. Setting this to 0.8 would return all contracts where either 80% of vol transacted on the ask or bid side

Examples:
0.19
min_strike
string
The minimum strike.

Examples:
120.5
min_sweep_volume_ratio
string
The minimum sweep volume ratio. Acceptable range: 0.00 to 1.00.

Examples:
0.15
min_theta
string
The minimum theta. Acceptable range: -inf to 0.00.

Examples:
-0.10
min_transactions
integer
The minimum number of transactions.

Examples:
10
min_underlying_price
string
The minimum stock price.

Examples:
5.23
min_vega
string
The minimum vega. Acceptable range: 0.00 to +inf.

Examples:
0.05
min_volume
integer
The minimum volume on that contract.

Examples:
12300
min_volume_oi_ratio
string
The minimum contract volume to open interest ratio.

Examples:
0.32
min_volume_ticker_vol_ratio
string
The minimum ratio of contract volume to total option volume of the underlying. Acceptable range: 0.00 to 1.00.

Examples:
0.25
order
string
The field to order by.

Allowed values:
bid_ask_vol
bull_bear_vol
contract_pricing
daily_perc_change
diff
dte
earnings
expires
expiry
floor_volume
floor_volume_ratio
from_high
from_low
iv
multileg_volume
open_interest
premium
spread
stock_price
tape_time
ticker
total_multileg_volume_ratio
trades
volume
volume_oi_ratio
volume_ticker_vol_ratio
Example:
volume
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
sectors[]
array[string]
An array of 1 or more sectors.

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
["Consumer Cyclical","Technology","Utilities"]
ticker_symbol
string
A comma separated list of tickers. To exclude certain tickers prefix the first ticker with a -.

Example:
AAPL,INTC
type
string
The option type to filter by if specified.

Allowed values:
call
Call
put
Put
vol_greater_oi
boolean
Only include contracts where the volume is greater than the open interest.

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
ask_side_volume
integer
The amount of volume that happened on the ask side.Show all...

Example:
119403
avg_price
string
The volume weighted average fill price of the contract.

Example:
1.0465802437910297887119234370
bid_side_volume
integer
The amount of volume that happened on the bid side.Show all...

Example:
122789
chain_prev_close
string
The previous trading day's contract price.

Example:
1.29
close
string
The last fill on the contract.

Example:
0.03
cross_volume
integer
The amount of cross volume. Cross volume consists of all transaction that have the cross trade code.

Example:
0
er_time
string
The time when the earnings will be released.

Allowed values:
unknown
afterhours
premarket
Example:
premarket
floor_volume
integer
The amount of floor volume. Floor volume consists of all transaction that have the floor trade code.

Example:
142
high
string
The highest fill on that contract.

Example:
2.95
last_fill
string
The last time there was a transaction for the given contract as UTC timestamp.

Example:
2023-09-08T17:45:32Z
low
string
The lowest fill on that contract.

Example:
0.02
mid_volume
integer
The amount of volume that happened in the middle of the ask and bid.Show all...

Example:
22707
multileg_volume
integer
The amount of volume that happened as part of a multileg trade with another contract. This can be spreads/rolls/condors/butterflies and more.

Example:
7486
next_earnings_date
string<date>
The next earnings date of the ticker. Null if either unknown as of now or if the ticker does not have any earnings such as an ETF

Example:
2023-10-26
no_side_volume
integer
The amount of volume that happened on no identifiable side. This can be late, out of sequence and/or cross transactions.

Example:
0
open
string
The first fill on that contract.

Example:
0.92
open_interest
integer
The open interest for the contract.

Example:
18680
option_symbol
string
The option symbol of the contract.Show all...

premium
string
The total option premium.

Example:
27723806.00
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
stock_multi_leg_volume
integer
The amount of volume that happened as part of a stock transaction and possibly other option contracts. This can be covered calls and more.

Example:
52
stock_price
string
The close stock price of the ticker.

Example:
182.91
sweep_volume
integer
The amount of sweep volume. Sweep volume consists of all transaction that have the sweep trade code.

Example:
18260
ticker_vol
integer
The total amount of options volume for the given ticker.

total_ask_changes
integer
The amount of time the ask changed for the given contract.

Example:
44343
total_bid_changes
integer
The amount of time the bid changed for the given contract.

Example:
43939
trades
integer
The amount of transaction for this contract.

Example:
39690
volume
integer
The contract volume.

Example:
264899
Token
:
123
date
:
string
exclude_ex_div_ticker
:
Not SetFalseTrue

select an option
expiry_dates[]
:
array
is_otm
:
Not SetFalseTrue

select an option
issue_types[]
:
array
limit
:
defaults to: 1
max_ask_perc
:
example: 0.45
max_ask_side_perc_7_day
:
example: 0.45
max_avg_price
:
example: 25.00
max_bear_perc
:
example: 0.45
max_bid_perc
:
example: 0.45
max_bid_side_perc_7_day
:
example: 0.45
max_bull_perc
:
example: 0.45
max_close
:
example: 25.00
max_daily_perc_change
:
example: 0.6
max_days_of_oi_increases
:
example: 10
max_days_of_vol_greater_than_oi
:
example: 7
max_delta
:
example: 0.80
max_diff
:
example: 1.34
max_dte
:
example: 3
max_earnings_dte
:
example: 30
max_floor_volume
:
example: 55800
max_floor_volume_ratio
:
example: 0.45
max_from_high_perc
:
example: 0.45
max_from_low_perc
:
example: 0.45
max_gamma
:
example: 0.15
max_iv_perc
:
example: 0.45
max_marketcap
:
example: 250000000
max_multileg_volume_ratio
:
example: 0.5
max_oi_change
:
example: 5000
max_oi_change_perc
:
example: 0.50
max_open_interest
:
example: 55600
max_perc_change
:
example: 0.68
max_premium
:
example: 53100.32
max_return_on_capital_perc
:
example: 0.45
max_skew_perc
:
example: 0.45
max_strike
:
example: 1200
max_sweep_volume_ratio
:
example: 0.75
max_theta
:
example: -0.01
max_transactions
:
example: 500
max_underlying_price
:
example: 10.53
max_vega
:
example: 0.25
max_volume
:
example: 55600
max_volume_oi_ratio
:
example: 1.58
max_volume_ticker_vol_ratio
:
example: 0.85
min_ask_perc
:
example: 0.19
min_ask_side_perc_7_day
:
example: 0.19
min_avg_price
:
example: 1.50
min_bear_perc
:
example: 0.19
min_bid_perc
:
example: 0.19
min_bid_side_perc_7_day
:
example: 0.19
min_bull_perc
:
example: 0.19
min_close
:
example: 1.50
min_daily_perc_change
:
example: 0.2
min_days_of_oi_increases
:
example: 3
min_days_of_vol_greater_than_oi
:
example: 2
min_delta
:
example: -0.50
min_diff
:
example: 0.53
min_dte
:
example: 1
min_earnings_dte
:
example: 1
min_floor_volume
:
example: 12300
min_floor_volume_ratio
:
example: 0.2
min_from_high_perc
:
example: 0.19
min_from_low_perc
:
example: 0.19
min_gamma
:
example: 0.01
min_iv_perc
:
example: 0.19
min_marketcap
:
example: 1000000
min_multileg_volume_ratio
:
example: 0.3
min_oi_change
:
example: -1000
min_oi_change_perc
:
example: -0.25
min_open_interest
:
example: 12300
min_perc_change
:
example: 0.5
min_premium
:
example: 12500.5
min_return_on_capital_perc
:
example: 0.19
min_skew_perc
:
example: 0.19
min_strike
:
example: 120.5
min_sweep_volume_ratio
:
example: 0.15
min_theta
:
example: -0.10
min_transactions
:
example: 10
min_underlying_price
:
example: 5.23
min_vega
:
example: 0.05
min_volume
:
example: 12300
min_volume_oi_ratio
:
example: 0.32
min_volume_ticker_vol_ratio
:
example: 0.25
order
:
Not Setbid_ask_volbull_bear_volcontract_pricingdaily_perc_changediffdteearningsexpiresexpiryfloor_volumefloor_volume_ratiofrom_highfrom_lowivmultileg_volumeopen_interestpremiumspreadstock_pricetape_timetickertotal_multileg_volume_ratiotradesvolumevolume_oi_ratiovolume_ticker_vol_ratio

select an option
order_direction
:
Not Setdescasc

select an option (defaults to: desc)
page
:
integer
sectors[]
:
array
ticker_symbol
:
string
type
:
Not SetcallCallputPut

select an option
vol_greater_oi
:
Not SetFalseTrue

select an option
