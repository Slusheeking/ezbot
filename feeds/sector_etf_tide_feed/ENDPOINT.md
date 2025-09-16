Exposure
get
https://api.unusualwhales.com/api/etfs/{ticker}/exposure
Returns all ETFs in which the given ticker is a holding

Request
Path Parameters
ticker
string
required
A single ticker

Example:
AAPL
Responses
200
Body

application/json

application/json
Returns the ETFs in which the given ticker is a holding

etf
string
The ticker of the ETF.

Example:
VTI
full_name
string
The full name of the ETF.

Example:
SPDR S&P 500 ETF Trust
last_price
string
The closing price of the candle.

Example:
56.79
prev_price
string
The previous trading day's stock price of the ticker.

Example:
189.70
shares
integer
The amount of shares that the ETF holds.

Example:
48427939
weight
string
The weight in percentage that the position represents in the ETF.

Example:
0.35
Token
:
123
ticker*
:
string
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/etfs/{ticker}/exposure \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "etf": "VTI",
      "full_name": "VANGUARD TOTAL STOCK MARKET INDEX FUND",
      "last_price": "236.16",
      "prev_price": "235.25",
      "shares": 130464268,
      "weight": "0.35"
    },
    {
      "etf": "VOO",
      "full_name": "VANGUARD 500 INDEX FUND",
      "last_price": "435.2",
      "prev_price": "433.19",
      "shares": 102076425,
      "weight": "0.49"
    },
    {
      "etf": "QQQ",
      "full_name": "INVESCO QQQ",
      "last_price": "405.97",
      "prev_price": "404.96",
      "shares": 75412427,
      "weight": "1.566"
    },
    {
      "etf": "SPY",
      "full_name": "SPDR S&P 500 ETF",
      "last_price": "471.55",
      "prev_price": "469.37",
      "shares": 48427939,
      "weight": "0.476355"
    }
  ]
}

Holdings
get
https://api.unusualwhales.com/api/etfs/{ticker}/holdings
Returns the holdings of the ETF

Request
Path Parameters
ticker
string
required
A single ticker

Example:
AAPL
Responses
200
Body

application/json

application/json
avg30_volume
string
The avg stock volume for the stock last 30 days.

Example:
55973002
bearish_premium
string
The bearish premium is defined as (call premium bid side) + (put premium ask side).

Example:
143198625
bullish_premium
string
The bullish premium is defined as (call premium ask side) + (put premium bid side).

Example:
196261414
call_premium
string
The sum of the premium of all the call transactions that executed.

Example:
9908777.0
call_volume
integer
The sum of the size of all the call transactions that executed.

Example:
990943
close
string
The closing price of the candle.

Example:
56.79
has_options
boolean
Boolean flag whether the company has options.

Example:
true
high
string
The highest price of the candle.

Example:
58.12
low
string
The lowest price of the candle.

Example:
51.90
name
string
The name of the company.

Example:
APPLE INC
open
string
The opening price of the candle.

Example:
54.29
prev_price
string
The previous trading day's stock price of the ticker.

Example:
189.70
put_premium
string
The sum of the premium of all the put transactions that executed.

Example:
163537151
put_volume
integer
The sum of the size of all the put transactions that executed.

Example:
808326
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
ticker
string
The stock ticker.

Example:
AAPL
volume
integer
The volume of the ticker for the trading day.

Example:
23132119
week_52_high
string
The 52 week high stock price of the ticker.

Example:
198.23
week_52_low
string
The 52 week low stock price of the ticker.

Example:
124.17
Token
:
123
ticker*
:
string
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/etfs/{ticker}/holdings \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "avg30_volume": "52433648",
      "bearish_premium": "32565174",
      "bullish_premium": "22987045",
      "call_premium": "45254976",
      "call_volume": 197685,
      "close": "194.84",
      "has_options": true,
      "high": "196.579",
      "low": "194.41",
      "name": "APPLE INC",
      "prev_price": "197.14",
      "put_premium": "16338631",
      "put_volume": 106773,
      "sector": "Technology",
      "shares": 169938760,
      "short_name": "APPLE",
      "ticker": "AAPL",
      "type": "stock",
      "volume": 12314310,
      "week52_high": "199.62",
      "week52_low": "123.15",
      "weight": "7.335"
    },
    {
      "avg30_volume": "30239291",
      "bearish_premium": "14318236",
      "bullish_premium": "14142305",
      "call_premium": "22499010",
      "call_volume": 48302,
      "close": "371.0",
      "has_options": true,
      "high": "371.0",
      "low": "368.73",
      "name": "MICROSOFT CORP",
      "prev_price": "369.36",
      "put_premium": "8688334",
      "put_volume": 35055,
      "sector": "Technology",
      "shares": 85913823,
      "short_name": "MICROSOFT",
      "ticker": "MSFT",
      "type": "stock",
      "volume": 3760724,
      "week52_high": "384.3",
      "week52_low": "216.98",
      "weight": "6.959"
    },
    {
      "avg30_volume": "51068229",
      "bearish_premium": "27305757",
      "bullish_premium": "37477652",
      "call_premium": "68914858",
      "call_volume": 243442,
      "close": "152.82",
      "has_options": true,
      "high": "152.9",
      "low": "150.09",
      "name": "AMAZON.COM INC",
      "prev_price": "149.6",
      "put_premium": "15242490",
      "put_volume": 86301,
      "sector": "Consumer Cyclical",
      "shares": 104991822,
      "short_name": "AMAZON",
      "ticker": "AMZN",
      "type": "stock",
      "volume": 11285233,
      "week52_high": "150.57",
      "week52_low": "81.43",
      "weight": "3.44"
    }
  ]
}


Inflow & Outflow
get
https://api.unusualwhales.com/api/etfs/{ticker}/in-outflow
Returns an ETF's inflow and outflow

Request
Path Parameters
ticker
string
required
A single ticker

Example:
AAPL
Responses
200
Body

application/json

application/json
change
integer
The net in/outflow measured as volume.

Example:
-50
change_prem
string
The net in/outflow measured as premium.

Example:
-5023.50
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
is_fomc
boolean
If the date has an FOMC announcement.

Example:
false
volume
integer
The volume of the ticker for the trading day.

Example:
23132119
Token
:
123
ticker*
:
string
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/etfs/{ticker}/in-outflow \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "change": -50,
      "change_prem": "-12000.0",
      "close": "236.16",
      "date": "2024-10-02",
      "is_fomc": false,
      "volume": 592342
    },
    {
      "change": 100,
      "change_prem": "23500.0",
      "close": "235.12",
      "date": "2024-10-01",
      "is_fomc": false,
      "volume": 602342
    }
  ]
}

Information
get
https://api.unusualwhales.com/api/etfs/{ticker}/info
Returns the information about the given ETF ticker.

Request
Path Parameters
ticker
string
required
A single ticker

Example:
AAPL
Responses
200
422
500
Body

application/json

application/json
aum
string
The total assets under management (AUM) of the ETF.

Example:
428887833900
avg30_volume
string
The avg stock volume for the stock last 30 days.

Example:
55973002
call_vol
integer
The sum of the size of all the call transactions that executed.

Example:
990943
description
string
Information about the ETF.

Example:
The Trust seeks to achieve its investment objective by holding a portfolio of the common stocks that are included in the index (the “Portfolio”), with the weight of each stock in the Portfolio substantially corresponding to the weight of such stock in the index.
domicile
string
The domicile of the ETF.

Example:
US
etf_company
string
The company which oversees the ETF.

Example:
SPDR
expense_ratio
string
The expense ratio of the ETF.

Example:
0.0945
has_options
boolean
Boolean flag whether the company has options.

Example:
true
holdings_count
integer
The amount of holdings the ETF has.

Example:
503
inception_date
string
The inception date of the ETF as an ISO date.

Example:
1993-01-22
name
string
The full name of the ETF.

Example:
SPDR S&P 500 ETF Trust
opt_vol
integer
The total options volume traded for the last trading day.

Example:
533227
put_vol
integer
The sum of the size of all the put transactions that executed.

Example:
808326
stock_vol
integer
The volume of the ticker for the trading day.

Example:
23132119
website
string
A link to the website of the ETF.

Example:
https://www.ssga.com/us/en/institutional/etfs/funds/spdr-sp-500-etf-trust-spy
Token
:
123
ticker*
:
string
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/etfs/{ticker}/info \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": {
    "aum": "428887833900",
    "avg30_volume": "73784934",
    "call_vol": 284364,
    "description": "The Trust seeks to achieve its investment objective by holding a portfolio of the common stocks that are included in the index (the “Portfolio”), with the weight of each stock in the Portfolio substantially corresponding to the weight of such stock in the index.",
    "domicile": "US",
    "etf_company": "SPDR",
    "expense_ratio": "0.0945",
    "has_options": true,
    "holdings_count": 503,
    "inception_date": "1993-01-22",
    "name": "SPDR S&P 500 ETF Trust",
    "opt_vol": 533227,
    "put_vol": 248863,
    "stock_vol": 4348819,
    "website": "https://www.ssga.com/us/en/institutional/etfs/funds/spdr-sp-500-etf-trust-spy"
  }
}

Sector & Country weights
get
https://api.unusualwhales.com/api/etfs/{ticker}/weights
Returns the sector & country weights for the given ETF ticker.

Request
Path Parameters
ticker
string
required
A single ticker

Example:
AAPL
Responses
200
422
500
Body

application/json

application/json
country
array[object]
A list of countries with their exposure by percentage.

Example:
[ { "country": "Netherlands", "weight": "0.0015" }, { "country": "Canada", "weight": "0.0014" } ]
country
string
The country.

Example:
Ireland
weight
string
The country exposure in percentage.

Example:
0.0164
sector
array[object]
A list of sectors with their exposure by percentage.

Example:
[ { "sector": "Basic Materials", "weight": "0.022" }, { "sector": "Communication Services", "weight": "0.0861" } ]
sector
string
The sector.

Example:
Healthcare
weight
string
The sector exposure in percentage.

Example:
0.1272
Token
:
123
ticker*
:
string
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/etfs/{ticker}/weights \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "country": [
    {
      "country": "Ireland",
      "weight": "0.0164"
    },
    {
      "country": "Other",
      "weight": "0.0059"
    },
    {
      "country": "Switzerland",
      "weight": "0.0043"
    },
    {
      "country": "Netherlands",
      "weight": "0.0015"
    },
    {
      "country": "Canada",
      "weight": "0.0014"
    },
    {
      "country": "Bermuda",
      "weight": "0.0011"
    },
    {
      "country": "Israel",
      "weight": "0.0001"
    },
    {
      "country": "United States",
      "weight": "0.9693"
    }
  ],
  "sector": [
    {
      "sector": "Basic Materials",
      "weight": "0.022"
    },
    {
      "sector": "Communication Services",
      "weight": "0.0861"
    },
    {
      "sector": "Consumer Cyclical",
      "weight": "0.1091"
    },
    {
      "sector": "Consumer Defensive",
      "weight": "0.0626"
    },
    {
      "sector": "Energy",
      "weight": "0.041"
    },
    {
      "sector": "Financial Services",
      "weight": "0.125"
    },
    {
      "sector": "Healthcare",
      "weight": "0.1272"
    },
    {
      "sector": "Industrials",
      "weight": "0.0816"
    },
    {
      "sector": "Other",
      "weight": "0.00009999999999990905"
    },
    {
      "sector": "Real Estate",
      "weight": "0.0243"
    },
    {
      "sector": "Technology",
      "weight": "0.2971"
    },
    {
      "sector": "Utilities",
      "weight": "0.0239"
    }
  ]
}



Sector Etfs
get
https://api.unusualwhales.com/api/market/sector-etfs
Returns the current trading days statistics for the SPDR sector etfs

This can be used to build a market overview such as:

sectors etf
Request
Responses
200
500
Body

application/json

application/json
avg30_stock_volume
string
Avg 30 day stock volume.

Example:
74402355
avg_30_day_call_volume
string
Avg 30 day call volume.

Example:
679430.000000000000
avg_30_day_put_volume
string
Avg 30 day put volume.

Example:
401961.285714285714
avg_7_day_call_volume
string
Avg 7 day call volume.

Example:
679145.333333333333
avg_7_day_put_volume
string
Avg 7 day put volume.

Example:
388676.000000000000
bearish_premium
string
The bearish premium is defined as (call premium bid side) + (put premium ask side).

Example:
143198625
bullish_premium
string
The bullish premium is defined as (call premium ask side) + (put premium bid side).

Example:
196261414
call_premium
string
The sum of the premium of all the call transactions that executed.

Example:
9908777.0
call_volume
integer
The sum of the size of all the call transactions that executed.

Example:
990943
close
string
The closing price of the candle.

Example:
56.79
full_name
string
The name/sector of the SPDR sector ETF.

Example:
S&P 500 Index
high
string
The highest price of the candle.

Example:
58.12
low
string
The lowest price of the candle.

Example:
51.90
marketcap
string
The marketcap of the underlying ticker. If the issue type of the ticker is ETF then the marketcap represents the AUM.

Example:
2965813810400
open
string
The opening price of the candle.

Example:
54.29
prev_close
string
The previous trading day's stock price of the ticker.

Example:
189.70
prev_date
string
The date of the previous trading day in ISO format.

Example:
2023-09-07
put_premium
string
The sum of the premium of all the put transactions that executed.

Example:
163537151
put_volume
integer
The sum of the size of all the put transactions that executed.

Example:
808326
ticker
string
The stock ticker.

Example:
AAPL
volume
integer
The volume of the ticker for the trading day.

Example:
23132119
week_52_high
string
The 52 week high stock price of the ticker.

Example:
198.23
week_52_low
string
The 52 week low stock price of the ticker.

Example:
124.17
Token
:
123
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/market/sector-etfs \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "avg30_call_volume": "3636459.000000000000",
      "avg30_put_volume": "4796289.166666666667",
      "avg30_stock_volume": "74402355",
      "avg_30_day_call_volume": "3636459.000000000000",
      "avg_30_day_put_volume": "4796289.166666666667",
      "avg_7_day_call_volume": "3343061.285714285714",
      "avg_7_day_put_volume": "4521616.428571428571",
      "bearish_premium": "258905527",
      "bullish_premium": "238729761",
      "call_premium": "293824502",
      "call_volume": 1844830,
      "full_name": "S&P 500 Index",
      "high": "447.11",
      "last": "446.15",
      "low": "444.8",
      "marketcap": "406517275500",
      "open": "444.93",
      "prev_close": "444.85",
      "prev_date": "2023-09-07",
      "put_premium": "244159205",
      "put_volume": 2009005,
      "ticker": "SPY",
      "volume": 23132119,
      "week52_high": "459.44",
      "week52_low": "342.65"
    },
    {
      "avg30_call_volume": "1574.3333333333333333",
      "avg30_put_volume": "2571.6000000000000000",
      "avg30_stock_volume": "4773693",
      "avg_30_day_call_volume": "1574.3333333333333333",
      "avg_30_day_put_volume": "2571.6000000000000000",
      "avg_7_day_call_volume": "2003.0000000000000000",
      "avg_7_day_put_volume": "1208.2857142857142857",
      "bearish_premium": "25852",
      "bullish_premium": "30558",
      "call_premium": "37618",
      "call_volume": 319,
      "full_name": "Materials",
      "high": "82.145",
      "last": "81.96",
      "low": "81.55",
      "marketcap": "5607626400",
      "open": "81.67",
      "prev_close": "81.72",
      "prev_date": "2023-09-07",
      "put_premium": "27107",
      "put_volume": 250,
      "ticker": "XLB",
      "volume": 1582879,
      "week52_high": "85.86",
      "week52_low": "66.13"
    },
    {
      "avg30_call_volume": "2020.4000000000000000",
      "avg30_put_volume": "1831.2000000000000000",
      "avg30_stock_volume": "5018213",
      "avg_30_day_call_volume": "2020.4000000000000000",
      "avg_30_day_put_volume": "1831.2000000000000000",
      "avg_7_day_call_volume": "1677.2857142857142857",
      "avg_7_day_put_volume": "2283.4285714285714286",
      "bearish_premium": "524756",
      "bullish_premium": "249626",
      "call_premium": "711775",
      "call_volume": 855,
      "full_name": "Communication Services",
      "high": "67.26",
      "last": "67.08",
      "low": "66.78",
      "marketcap": "14026276000",
      "open": "66.78",
      "prev_close": "66.76",
      "prev_date": "2023-09-07",
      "put_premium": "261697",
      "put_volume": 1048,
      "ticker": "XLC",
      "volume": 1435724,
      "week52_high": "69.22",
      "week52_low": "44.63"
    }
  ]
}