FDA Calendar
get
https://api.unusualwhales.com/api/market/fda-calendar
Returns FDA calendar data with filtering options.

The FDA calendar contains information about:

PDUFA (Prescription Drug User Fee Act) dates
Advisory Committee Meetings
FDA Decisions
Clinical Trial Results
New Drug Applications
Biologics License Applications
Date Format Support
The target_date parameters support various FDA-specific date formats:

Quarters: YYYY-Q[1-4] (e.g. 2024-Q1)
Half years: YYYY-H[1-2] (e.g. 2024-H1)
Mid-year: YYYY-MID (e.g. 2024-MID)
Late-year: YYYY-LATE (e.g. 2024-LATE)
Standard dates: YYYY-MM-DD
Request
Query Parameters
announced_date_max
string
Maximum announced date (YYYY-MM-DD)

Example:
2024-01-18
announced_date_min
string
Minimum announced date (YYYY-MM-DD)

Example:
2024-01-18
drug
string
Filter by drug name (partial match)

Example:
Keytruda
limit
integer
Maximum number of results to return

>= 1
<= 200
Default:
100
Example:
10
target_date_max
string
Maximum target date (supports Q1-Q4, H1-H2, MID, LATE formats)

Example:
2024-Q1
Match pattern:
^\d{4}-(Q[1-4]|H[1-2]|MID|LATE|\d{2}-\d{2})$
target_date_min
string
Minimum target date (supports Q1-Q4, H1-H2, MID, LATE formats)

Example:
2024-Q1
Match pattern:
^\d{4}-(Q[1-4]|H[1-2]|MID|LATE|\d{2}-\d{2})$
ticker
string
Filter by ticker symbol

Example:
AAPL,INTC
Responses
200
500
FDA Calendar response

Body

application/json

application/json
FDA calendar events with company information

catalyst
string
The type of FDA event (e.g., PDUFA Date, Advisory Committee Meeting)

Example:
PDUFA Date
description
string
Detailed description of the FDA event

Example:
FDA decision for Lifileucel in advanced melanoma
drug
string
required
Name of the drug under FDA review

Example:
Lifileucel
end_date
string<date>
required
The end date of the FDA event

Example:
2024-02-24
has_options
boolean or null
Whether the company has options available for trading

Example:
true
indication
string
The medical condition the drug is intended to treat

Example:
Advanced Melanoma
marketcap
string or null
The company's market capitalization in USD

Example:
1000000000
notes
string or null
Additional important notes about the FDA event

Example:
Important milestone for the company's drug pipeline
outcome
string or null
The outcome of the FDA event if already occurred

Example:
Approved
outcome_brief
string or null
Brief summary of the FDA event outcome

Example:
Complete Response Letter received
source_link
string or null
Link to the source of the FDA event information

Example:
https://www.fda.gov/news-events/press-announcements/fda-example
start_date
string<date>
required
The start date of the FDA event

Example:
2024-02-24
status
string
required
The current status of the FDA application (e.g., NDA, BLA)

Example:
NDA
ticker
string
required
The ticker of the company applying for drug admission.

Example:
IOVA
Token
:
123
announced_date_max
:
string
announced_date_min
:
string
drug
:
string
limit
:
defaults to: 100
target_date_max
:
string
target_date_min
:
string
ticker
:
string
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/market/fda-calendar \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "catalyst": "PDUFA Date",
      "description": "FDA decision for Lifileucel in advanced melanoma",
      "drug": "Lifileucel",
      "end_date": "2024-02-24",
      "has_options": true,
      "indication": "Advanced Melanoma",
      "marketcap": "1000000000",
      "notes": "Important milestone for the company's drug pipeline",
      "outcome": null,
      "outcome_brief": null,
      "source_link": "https://www.fda.gov/news-events/press-announcements/fda-example",
      "start_date": "2024-02-24",
      "status": "NDA",
      "ticker": "IOVA"
    }
  ]
}


Economic calendar
get
https://api.unusualwhales.com/api/market/economic-calendar
Returns the economic calendar.

Request
Responses
200
500
Economic Calendar response

Body

application/json

application/json
responses
/
200
The economic calendar for the current & next week

event
string
The event/reason. Can be a fed speaker or an economic report/indicator

Example:
PCE index
forecast
string
The forecast if the event is an economic report/indicator

Example:
69.4
prev
string
The previous value of the preceding period if the event is an economic report/indicator

Example:
69.4
reported_period
string
The period for that the economic report/indicator is being reported.

Example:
December
time
string
The time at which the event will start as UTC timestamp.

Example:
2023-12-22T13:30:00Z
type
string
The type of the event

Allowed values:
fed-speaker
fomc
report
Example:
fomc
Token
:
123
Send API Request
curl --request GET \
  --url https://api.unusualwhales.com/api/market/economic-calendar \
  --header 'Accept: application/json, text/plain' \
  --header 'Authorization: Bearer 123'
{
  "data": [
    {
      "event": "Consumer sentiment (final)",
      "forecast": "69.4",
      "prev": "69.4",
      "reported_period": "December",
      "time": "2023-12-22T15:00:00Z",
      "type": "report"
    },
    {
      "event": "PCE index",
      "forecast": null,
      "prev": "0.0%",
      "reported_period": "November",
      "time": "2023-12-22T13:30:00Z",
      "type": "report"
    }
  ]
}