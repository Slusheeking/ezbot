Afterhours
get
https://api.unusualwhales.com/api/earnings/afterhours
Returns the afterhours earnings for a given date.

Request
Query Parameters
date
string
A trading date in the format of YYYY-MM-DD. This is optional and by default the last trading date.

Example:
2024-01-18
limit
integer
How many items to return. Default: 50. Max: 100. Min: 1.

>= 1
<= 100
Default:
50
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
responses
/
200
The earnings data for a date and report time.

actual_eps
string
Example:
1.44
continent
string
Example:
North America
country_code
string
Example:
US
country_name
string
Example:
UNITED STATES
ending_fiscal_quarter
string
An ISO date.

Example:
2024-01-09
expected_move
string
The expected earnings move in $.

Example:
1.23
expected_move_perc
string
The expected earnings move in %.

Example:
0.08
full_name
string
Example:
MICROSOFT CORP
has_options
boolean or null
Whether the company has options available for trading

Example:
true
is_s_p_500
boolean
marketcap
string
Example:
152983052
post_earnings_close
string
The close stock price of the ticker.

Example:
182.91
post_earnings_date
string
An ISO date.

Example:
2024-01-09
pre_earnings_close
string
The close stock price of the ticker.

Example:
182.91
pre_earnings_date
string
An ISO date.

Example:
2024-01-09
reaction
string
The 1D % stock move after the earnings report.

Example:
0.15
report_date
string
An ISO date.

Example:
2024-01-09
report_time
string
The earnings report time. Possible values include: premarket, postmarket and unknown

Example:
postmarket
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
source
string
The source of the report date. Either the report date comes from the company or it is an estimation. Possible values: company, estimation.

Example:
company
street_mean_est
string
The Street mean EPS estimates.

Example:
1.34
symbol
string
Example:
MSFT
Token
:
123
date
:
string
limit
:
defaults to: 50
page
:
integer
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/earnings/afterhours \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "actual_eps": "2.45",
      "continent": "North America",
      "country_code": "US",
      "country_name": "UNITED STATES",
      "ending_fiscal_quarter": "2022-12-31",
      "expected_move": "9.91",
      "expected_move_perc": "0.0359",
      "full_name": "INVENTRUST PROPERTIES",
      "has_options": true,
      "is_s_p_500": false,
      "marketcap": "1649115201",
      "post_earnings_close": "148.42",
      "post_earnings_date": "2023-02-14",
      "pre_earnings_close": "143.23",
      "pre_earnings_date": "2023-02-13",
      "reaction": "0.041",
      "report_date": "2023-02-14",
      "report_time": "postmarket",
      "sector": "Real Estate",
      "source": "company",
      "street_mean_est": "2.25",
      "symbol": "IVT"
    },
    {
      "actual_eps": "2.45",
      "continent": "Europe",
      "country_code": "LU",
      "country_name": "LUXEMBOURG",
      "ending_fiscal_quarter": "2022-12-31",
      "expected_move": "9.91",
      "expected_move_perc": "0.0359",
      "full_name": "TERNIUM SA",
      "has_options": true,
      "is_s_p_500": false,
      "marketcap": "7375279462",
      "post_earnings_close": "148.42",
      "post_earnings_date": "2023-02-14",
      "pre_earnings_close": "143.23",
      "pre_earnings_date": "2023-02-13",
      "reaction": "0.041",
      "report_date": "2023-02-14",
      "report_time": "postmarket",
      "sector": "Basic Materials",
      "source": "company",
      "street_mean_est": "2.25",
      "symbol": "TX"
    }
  ]
}


Premarket
get
https://api.unusualwhales.com/api/earnings/premarket
Returns the premarket earnings for a given date.

Request
Query Parameters
date
string
A trading date in the format of YYYY-MM-DD. This is optional and by default the last trading date.

Example:
2024-01-18
limit
integer
How many items to return. Default: 50. Max: 100. Min: 1.

>= 1
<= 100
Default:
50
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
responses
/
200
The earnings data for a date and report time.

actual_eps
string
Example:
1.44
continent
string
Example:
North America
country_code
string
Example:
US
country_name
string
Example:
UNITED STATES
ending_fiscal_quarter
string
An ISO date.

Example:
2024-01-09
expected_move
string
The expected earnings move in $.

Example:
1.23
expected_move_perc
string
The expected earnings move in %.

Example:
0.08
full_name
string
Example:
MICROSOFT CORP
has_options
boolean or null
Whether the company has options available for trading

Example:
true
is_s_p_500
boolean
marketcap
string
Example:
152983052
post_earnings_close
string
The close stock price of the ticker.

Example:
182.91
post_earnings_date
string
An ISO date.

Example:
2024-01-09
pre_earnings_close
string
The close stock price of the ticker.

Example:
182.91
pre_earnings_date
string
An ISO date.

Example:
2024-01-09
reaction
string
The 1D % stock move after the earnings report.

Example:
0.15
report_date
string
An ISO date.

Example:
2024-01-09
report_time
string
The earnings report time. Possible values include: premarket, postmarket and unknown

Example:
postmarket
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
source
string
The source of the report date. Either the report date comes from the company or it is an estimation. Possible values: company, estimation.

Example:
company
street_mean_est
string
The Street mean EPS estimates.

Example:
1.34
symbol
string
Example:
MSFT
Token
:
123
date
:
string
limit
:
defaults to: 50
page
:
integer
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/earnings/premarket \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "actual_eps": "2.45",
      "continent": "North America",
      "country_code": "US",
      "country_name": "UNITED STATES",
      "ending_fiscal_quarter": "2022-12-31",
      "expected_move": "9.91",
      "expected_move_perc": "0.0359",
      "full_name": "INVENTRUST PROPERTIES",
      "has_options": true,
      "is_s_p_500": false,
      "marketcap": "1649115201",
      "post_earnings_close": "148.42",
      "post_earnings_date": "2023-02-14",
      "pre_earnings_close": "143.23",
      "pre_earnings_date": "2023-02-13",
      "reaction": "0.041",
      "report_date": "2023-02-14",
      "report_time": "postmarket",
      "sector": "Real Estate",
      "source": "company",
      "street_mean_est": "2.25",
      "symbol": "IVT"
    },
    {
      "actual_eps": "2.45",
      "continent": "Europe",
      "country_code": "LU",
      "country_name": "LUXEMBOURG",
      "ending_fiscal_quarter": "2022-12-31",
      "expected_move": "9.91",
      "expected_move_perc": "0.0359",
      "full_name": "TERNIUM SA",
      "has_options": true,
      "is_s_p_500": false,
      "marketcap": "7375279462",
      "post_earnings_close": "148.42",
      "post_earnings_date": "2023-02-14",
      "pre_earnings_close": "143.23",
      "pre_earnings_date": "2023-02-13",
      "reaction": "0.041",
      "report_date": "2023-02-14",
      "report_time": "postmarket",
      "sector": "Basic Materials",
      "source": "company",
      "street_mean_est": "2.25",
      "symbol": "TX"
    }
  ]
}


Historical Ticker Earnings
get
https://api.unusualwhales.com/api/earnings/{ticker}
Returns the historical earnings for the given ticker.

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
responses
/
200
The earnings data for a ticker and date.

actual_eps
string
Example:
1.44
ending_fiscal_quarter
string
An ISO date.

Example:
2024-01-09
expected_move
string
The expected earnings move in $.

Example:
1.23
expected_move_perc
string
The expected earnings move in %.

Example:
0.08
long_straddle_1d
string
The 1 day % returns for the closest expiry long ATM straddle. The straddle expiry is equal to or greater than 1 day after earnings.

Example:
0.3421
long_straddle_1w
string
The 1 week % returns for the closest expiry long ATM straddle. The straddle expiry is equal to or greater than 1 week after earnings.

Example:
0.3421
post_earnings_move_1d
string
The 1 day % move after the earnings report.

Example:
0.08
post_earnings_move_1w
string
The 1 week % move after the earnings report.

Example:
0.08
post_earnings_move_2w
string
The 2 week % move after the earnings report.

Example:
0.08
post_earnings_move_3d
string
The 3 day % move after the earnings report.

Example:
0.08
pre_earnings_move_1d
string
The 1 day % move up to the earnings report.

Example:
0.08
pre_earnings_move_1w
string
The 1 week % move up to the earnings report.

Example:
0.08
pre_earnings_move_2w
string
The 2 week % move up to the earnings report.

Example:
0.08
pre_earnings_move_3d
string
The 3 day % move up to the earnings report.

Example:
0.08
report_date
string
An ISO date.

Example:
2024-01-09
report_time
string
The earnings report time. Possible values include: premarket, postmarket and unknown

Example:
postmarket
short_straddle_1d
string
The 1 day % returns for the closest expiry short ATM straddle. The straddle expiry is equal to or greater than 1 day after earnings.

Example:
0.3421
short_straddle_1w
string
The 1 week % returns for the closest expiry short ATM straddle. The straddle expiry is equal to or greater than 1 week after earnings.

Example:
0.3421
source
string
The source of the report date. Either the report date comes from the company or it is an estimation. Possible values: company, estimation.

Example:
company
street_mean_est
string
The Street mean EPS estimates.

Example:
1.34
Token
:
123
ticker*
:
string
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/earnings/{ticker} \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "actual_eps": "2.45",
      "ending_fiscal_quarter": "2024-09-30",
      "expected_move": "9.91",
      "expected_move_perc": "0.0359",
      "long_straddle_1d": "0.2349",
      "long_straddle_1w": "0.0129",
      "post_earnings_move_1d": "0.0724",
      "post_earnings_move_1w": "0.132",
      "post_earnings_move_2w": "0.1582",
      "post_earnings_move_3d": "0.0231",
      "pre_earnings_move_1d": "0.0724",
      "pre_earnings_move_1w": "0.132",
      "pre_earnings_move_2w": "0.1582",
      "pre_earnings_move_3d": "0.0231",
      "report_date": "2024-11-10",
      "report_time": "postmarket",
      "short_straddle_1d": "-0.5830",
      "short_straddle_1w": "-0.005",
      "source": "company",
      "street_mean_est": "2.25"
    },
    {
      "actual_eps": "2.32",
      "ending_fiscal_quarter": "2024-06-30",
      "expected_move": "8.23",
      "expected_move_perc": "0.0261",
      "long_straddle_1d": "0.2349",
      "long_straddle_1w": "0.0129",
      "post_earnings_move_1d": "0.0724",
      "post_earnings_move_1w": "0.132",
      "post_earnings_move_2w": "0.1582",
      "post_earnings_move_3d": "0.0231",
      "pre_earnings_move_1d": "0.0724",
      "pre_earnings_move_1w": "0.132",
      "pre_earnings_move_2w": "0.1582",
      "pre_earnings_move_3d": "0.0231",
      "report_date": "2024-08-02",
      "report_time": "postmarket",
      "short_straddle_1d": "-0.5830",
      "short_straddle_1w": "-0.005",
      "source": "company",
      "street_mean_est": "2.15"
    }
  ]
}