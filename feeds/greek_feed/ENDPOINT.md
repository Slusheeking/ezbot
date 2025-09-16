Greek flow by expiry
get
https://api.unusualwhales.com/api/group-flow/{flow_group}/greek-flow/{expiry}
Returns the group flow's greek flow (delta & vega flow) for the given market day broken down per minute & expiry. Date must be the current or a past date. If no date is given, returns data for the current/last market day.

Request
Path Parameters
expiry
string
required
A single expiry date in ISO date format.

Example:
2024-02-02
flow_group
string
required
A flow group

Allowed values:
airline
bank
basic materials
china
communication services
consumer cyclical
consumer defensive
crypto
cyber
energy
financial services
gas
gold
healthcare
industrials
mag7
oil
real estate
refiners
reit
semi
silver
technology
uranium
utilities
Example:
airline
Query Parameters
date
string
A trading date in the format of YYYY-MM-DD. This is optional and by default the last trading date.

Example:
2024-01-18
Responses
200
Body

application/json

application/json
responses
/
200
Greek flow by flow group, minute timestamps, and expiry date.

dir_delta_flow
string
The directional delta flow.

Example:
-43593.96
dir_vega_flow
string
The directional vega flow.

Example:
31243.04
expiry
string
The contract expiry date in ISO format.

Example:
2023-12-22
flow_group
string
A flow group where the flow data for all tickers in that group are aggregated.

Allowed values:
airline
bank
basic materials
china
communication services
consumer cyclical
consumer defensive
crypto
cyber
energy
financial services
gas
gold
healthcare
industrials
mag7
oil
real estate
refiners
reit
semi
silver
technology
uranium
utilities
Example:
airline
net_call_premium
string
Defined as (call premium ask side) - (call premium bid side).

Example:
-29138464
net_call_volume
integer
Defined as (call volume ask side) - (call volume bid side).

Example:
1049
net_put_premium
string
Defined as (put premium ask side) - (put premium bid side).

Example:
23924325
net_put_volume
integer
Defined as (put volume ask side) - (put volume bid side).

Example:
1313
otm_dir_delta_flow
string
The directional delta flow of out-of-the-money options.

Example:
14947.51
otm_dir_vega_flow
string
The directional vega flow of out-of-the-money options.

Example:
11421.03
otm_total_delta_flow
string
The total delta flow of out-of-the-money options.

Example:
-28564.02
otm_total_vega_flow
string
The total vega flow of out-of-the-money options.

Example:
101745.64
timestamp
string<date-time>
The (start of minute) timestamp of the data.

Example:
2024-10-28T18:46:00Z
total_delta_flow
string
The total delta flow.

Example:
-21257.36
total_vega_flow
string
The total vega flow.

Example:
350944.58
transactions
integer
The amount of transactions.

Example:
1188
volume
integer
The total options volume.

Example:
12348
Token
:
123
expiry*
:
string
flow_group*
:
airlinebankbasic materialschinacommunication servicesconsumer cyclicalconsumer defensivecryptocyberenergyfinancial servicesgasgoldhealthcareindustrialsmag7oilreal estaterefinersreitsemisilvertechnologyuraniumutilities

airline
date
:
string
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/group-flow/airline/greek-flow/{expiry} \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "dir_delta_flow": "-43593.96",
      "dir_vega_flow": "31243.04",
      "expiry": "2024-10-28",
      "flow_group": "airline",
      "net_call_premium": "-1095135.00",
      "net_call_volume": 1049,
      "net_put_premium": "135732.00",
      "net_put_volume": 415,
      "otm_dir_delta_flow": "14947.51",
      "otm_dir_vega_flow": "11421.03",
      "otm_total_delta_flow": "-28564.02",
      "otm_total_vega_flow": "101745.64",
      "timestamp": "2024-10-28T18:46:00Z",
      "total_delta_flow": "-21257.36",
      "total_vega_flow": "350944.58",
      "transactions": 1188,
      "volume": 12348
    }
  ]
}


Greek flow
get
https://api.unusualwhales.com/api/group-flow/{flow_group}/greek-flow
Returns the group flow's greek flow (delta & vega flow) for the given market day broken down per minute. Date must be the current or a past date. If no date is given, returns data for the current/last market day.

Request
Path Parameters
flow_group
string
required
A flow group

Allowed values:
airline
bank
basic materials
china
communication services
consumer cyclical
consumer defensive
crypto
cyber
energy
financial services
gas
gold
healthcare
industrials
mag7
oil
real estate
refiners
reit
semi
silver
technology
uranium
utilities
Example:
airline
Query Parameters
date
string
A trading date in the format of YYYY-MM-DD. This is optional and by default the last trading date.

Example:
2024-01-18
Responses
200
Body

application/json

application/json
Greek flow by flow group and minute timestamps.

dir_delta_flow
string
The directional delta flow.

Example:
-43593.96
dir_vega_flow
string
The directional vega flow.

Example:
31243.04
flow_group
string
A flow group where the flow data for all tickers in that group are aggregated.

Allowed values:
airline
bank
basic materials
china
communication services
consumer cyclical
consumer defensive
crypto
cyber
energy
financial services
gas
gold
healthcare
industrials
mag7
oil
real estate
refiners
reit
semi
silver
technology
uranium
utilities
Example:
airline
net_call_premium
string
Defined as (call premium ask side) - (call premium bid side).

Example:
-29138464
net_call_volume
integer
Defined as (call volume ask side) - (call volume bid side).

Example:
1049
net_put_premium
string
Defined as (put premium ask side) - (put premium bid side).

Example:
23924325
net_put_volume
integer
Defined as (put volume ask side) - (put volume bid side).

Example:
1313
otm_dir_delta_flow
string
The directional delta flow of out-of-the-money options.

Example:
14947.51
otm_dir_vega_flow
string
The directional vega flow of out-of-the-money options.

Example:
11421.03
otm_total_delta_flow
string
The total delta flow of out-of-the-money options.

Example:
-28564.02
otm_total_vega_flow
string
The total vega flow of out-of-the-money options.

Example:
101745.64
timestamp
string<date-time>
The (start of minute) timestamp of the data.

Example:
2024-10-28T18:46:00Z
total_delta_flow
string
The total delta flow.

Example:
-21257.36
total_vega_flow
string
The total vega flow.

Example:
350944.58
transactions
integer
The amount of transactions.

Example:
1188
volume
integer
The total options volume.

Example:
12348
Token
:
123
flow_group*
:
airlinebankbasic materialschinacommunication servicesconsumer cyclicalconsumer defensivecryptocyberenergyfinancial servicesgasgoldhealthcareindustrialsmag7oilreal estaterefinersreitsemisilvertechnologyuraniumutilities

airline
date
:
string
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/group-flow/airline/greek-flow \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "dir_delta_flow": "-43593.96",
      "dir_vega_flow": "31243.04",
      "flow_group": "airline",
      "net_call_premium": "-1095135.00",
      "net_call_volume": 1049,
      "net_put_premium": "135732.00",
      "net_put_volume": 415,
      "otm_dir_delta_flow": "14947.51",
      "otm_dir_vega_flow": "11421.03",
      "otm_total_delta_flow": "-28564.02",
      "otm_total_vega_flow": "101745.64",
      "timestamp": "2024-10-28T18:46:00Z",
      "total_delta_flow": "-21257.36",
      "total_vega_flow": "350944.58",
      "transactions": 1188,
      "volume": 12348
    }
  ]
}