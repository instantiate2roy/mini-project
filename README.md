# OOP with Python: Assignment 2 mini-projects

Mini-projects from Assignment 2 (Advent 2026). Each one has its own notebook, with the reusable classes in `src/` and pytest tests in `tests/`.

| Notebook | Mini-project |
|---|---|
| `project1_weather_forecast.ipynb` | 1. Fetching and displaying a weather forecast with Python web APIs: geocodes a place name, downloads a forecast from Open-Meteo and MET Norway, and shows it as a table, a summary and a chart |
| `project2_tax_engine.ipynb` | 2. Uganda tax engine: PAYE, a payroll pipeline (NSSF, Local Service Tax, PAYE and net pay), VAT, corporate income tax, and withholding and rental income tax |

## Setup

You need Python 3.10 or newer.

```bash
git clone https://github.com/instantiate2roy/mini-project.git
cd mini-project
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## How to run

1. Open each notebook from the project folder, so that `src` and `configs` can be found:

   ```bash
   jupyter notebook project1_weather_forecast.ipynb
   jupyter notebook project2_tax_engine.ipynb
   ```

2. For mini-project 1, create a file called `.env` in the project folder (next to this README, not inside `src/`) with your own university email:

   ```
   MET_API_EMAIL=your.name@university.ac.ug
   ```

   MET Norway requires a contact email in the `User-Agent` header of every request, so it can reach you about your traffic. `.env` is listed in `.gitignore`, so the email is never committed. `load_dotenv()` looks in the project folder and its parent folders, so a `.env` inside `src/` is not found.
3. Choose **Kernel > Restart Kernel and Run All Cells**.
   - **Mini-project 1** needs an internet connection. Its configuration cell asks for a location, which is the only manual input. If a name matches several places (for example "Springfield"), you pick one from the list.
   - **Mini-project 2** needs no input and no internet connection. Every rate and band comes from `configs/tax.json`.

To run the tests, which work offline:

```bash
pytest
```

## Project structure

| Path | Contents |
|---|---|
| `project1_weather_forecast.ipynb` | Mini-project 1: urllib and requests compared, response details, forecast table and report, robustness tests, MET Norway as a second source, and the report on data flow, licensing, reliability and privacy |
| `src/weather_forecast.py` | `WeatherForecast`: abstract base class holding the contact email, with geocoding and the request wrapper (timeout, retries and exponential backoff) |
| `src/open_meteo.py` | `OpenMeteo`: daily forecast from Open-Meteo, with weather codes decoded into text |
| `src/met_norway.py` | `MetNorway`: MET Norway Locationforecast 2.0, with hourly and 6-hourly steps grouped into local days under the same column names as `OpenMeteo` |
| `src/weather_report.py` | `WeatherReport`: summary table, formatted forecast table, and temperature and precipitation chart |
| `src/http_request_exception.py` | `HttpRequestException`: raised when a request still fails after every retry |
| `project2_tax_engine.ipynb` | Mini-project 2: PAYE calculator, payroll pipeline and the order of deductions, VAT module, corporate income tax, and Extension A (withholding and rental income tax) |
| `configs/tax.json` | Uganda's tax rates, PAYE bands, LST brackets, VAT categories and WHT rates, read by every tax class |
| `src/tax.py` | `Tax`: abstract base class that loads the country's settings from `configs/tax.json` and defines `calculate(ctx: TaxContext) -> TaxResult` |
| `src/tax_context.py`, `src/tax_result.py` | `TaxContext` (the inputs) and `TaxResult` (the tax, its base and the employer's share), as frozen dataclasses |
| `src/money.py` | `Money`: UGX amount stored as a `Decimal`, rounded to whole shillings, with arithmetic and comparison operators |
| `src/error.py` | `TaxError` and its subclasses `InvalidIncomeError`, `NoScheduleForDateError`, `TaxConfigError` and `InvalidContextError` |
| `src/paye.py`, `src/nssf.py`, `src/lst.py` | PAYE (resident and non-resident bands), NSSF and Local Service Tax |
| `src/vat.py`, `src/cit.py` | VAT by supply category, and corporate income tax |
| `src/wht.py`, `src/rental.py` | Extension A: withholding tax by payment type, and rental income tax for individuals and companies |
| `tests/test_weather_forecast.py` | Mini-project 1: parsing, geocoding, requests, retries and the report |
| `tests/test_paye.py` | Mini-project 2: PAYE at every band edge, and hypothesis property tests |
| `tests/test_tax_engine.py` | Mini-project 2: `Money`, the error classes, the `Tax` base class, NSSF, LST, VAT and corporate income tax |
| `tests/test_wht_rental.py` | Mini-project 2: withholding and rental income tax, with hypothesis property tests |
| `tests/data/` | Sample JSON used by the mini-project 1 tests (see below) |

### Sample JSON for the offline tests

| File | Source |
|---|---|
| `geocode_kampala.json` | Open-Meteo Geocoding response for "Kampala", trimmed to one match |
| `geocode_springfield.json` | Open-Meteo Geocoding response for "Springfield", trimmed to three matches |
| `geocode_no_results.json` | Open-Meteo Geocoding response for a name with no match: it has no `results` key |
| `open_meteo_forecast_kampala.json` | Open-Meteo 7-day daily forecast for Kampala |
| `met_norway_compact_kampala.json` | Built by hand in the documented MET Norway `compact` format. It is not a real forecast: it is designed so the tests can check day grouping, time zone conversion and overlapping hourly and 6-hourly periods |

The Open-Meteo files were recorded from the live APIs on 8 October 2026.

## Data sources

- **Open-Meteo Geocoding API** (geocoding-api.open-meteo.com/v1/search): place name to latitude and longitude.
- **Open-Meteo Forecast API** (api.open-meteo.com/v1/forecast): main daily forecast. Open-Meteo data is licensed under CC BY 4.0.
- **MET Norway Locationforecast 2.0** (api.met.no/weatherapi/locationforecast/2.0): second source. MET Norway data is licensed under NLOD 2.0 and CC BY 4.0, and its terms require an identifying `User-Agent`.

## Libraries outside the brief's allowed list

| Library | Why |
|---|---|
| `python-dotenv` | Reads the contact email from `.env`, so it is not hardcoded in shared code |
| `jinja2` | pandas needs it for `DataFrame.style`, which formats the forecast table |
| `IPython.display` (installed with `ipykernel`) | Shows Markdown and styled tables from inside `src/` classes |
| `zoneinfo` and `collections` (standard library), `tzdata` | Convert MET Norway's UTC times to the location's local time; `tzdata` supplies time zone data on Windows |
| `pytest` | Runs the offline tests |
| `hypothesis` | Property-based tests for mini-project 2, which the brief requires |

## Findings

### Mini-project 1: Weather forecast

- **urllib and requests:** both return the same geocoding result. requests needs less code, encodes the query and decodes the JSON itself, and catches every failure through one exception class.
- **Response details:** the geocoding API answers with status 200 and `Content-Type: application/json`; the response time is printed for each run.
- **Two sources, one table:** Open-Meteo returns daily values directly. MET Norway only returns hourly and 6-hourly time steps in UTC, so `MetNorway` converts them to local time, groups them into days, and uses only the hourly rain where both periods overlap. Its table then has the same columns as Open-Meteo's, apart from wind in m/s instead of km/h.
- **Robustness:** an invalid city raises a clear `ValueError`. An invalid latitude (999) gets HTTP 400, which is not retried. With no network (simulated), a tiny timeout or repeated 5xx server errors, the request is tried 4 times with delays of 1, 2 and 4 seconds, then fails with `HttpRequestException`.

The full report (data flow, licensing, reliability and privacy) is at the end of the notebook.

### Mini-project 2: Uganda tax engine

- **PAYE:** all 15 sample incomes give the expected tax for both residency schedules. A resident earning UGX 1,000,000 a month pays 188,250, and one earning 12,000,000 pays 3,688,250, which includes the extra 10% on income above 10,000,000.
- **Payroll order:** Local Service Tax comes first because it is deducted before PAYE, then NSSF, then PAYE on gross pay minus LST, then net pay. An employee earning UGX 1,500,000 in July pays 25,000 LST, 330,750 PAYE (on 1,475,000) and 75,000 NSSF, leaving 1,069,250. The employer pays another 150,000 NSSF on top.
- **VAT:** on the sample invoices, output VAT on sales is UGX 2,610,000 and input VAT on purchases is 1,116,000, so 1,494,000 is payable. Zero-rated and exempt invoices both carry no VAT.
- **Corporate income tax:** revenue of UGX 880,000,000 minus allowable deductions of 435,000,000 leaves chargeable income of 445,000,000, taxed at 30%: 133,500,000. Another 98,000,000 of costs, such as fines and income tax paid, are not deductible.
- **Extension A:** withholding tax ranges from 5% (debenture interest paid abroad) to 15% (dividends, interest, royalties and betting winnings). Individuals pay 12% rental tax on annual rent above 2,820,000; companies pay 30% after expenses, which can cut chargeable rent by at most half.
- **Properties:** hypothesis checks thousands of incomes and finds that PAYE is never negative, never goes down when income goes up, and never exceeds income.

## AI-use declaration

I used AI tools while working on this project:

- **Claude (Anthropic):**
  - Building the tests (`tests/test_weather_forecast.py` and `tests/test_tax_engine.py`), the sample JSON in `tests/data/`, and `pytest.ini`, and updating `tests/test_wht_rental.py` to the current error messages.
  - Drafting this README and `requirements.txt`.
  - The fake connectivity simulation: replacing `requests.get` with a version that raises `ConnectionError`, and `time.sleep` with a recorder, so the no-network case and the retry delays can be shown without a real outage.
  - Code review of my code for correctness, for both mini-projects.
  - Getting the API request and response formats and their documentation for Open-Meteo Geocoding, Open-Meteo Forecast and MET Norway Locationforecast 2.0.
  - How to use MET Norway Locationforecast 2.0: the required `User-Agent`, coordinates limited to 4 decimals, the `compact` response format, and its mix of hourly and 6-hourly time steps.
  - Adding type hints to the class methods and attributes, for both mini-projects.
  - The 1,000–1,500 word write-up.

I wrote the original code and analysis. I reviewed all AI-generated code and text, and ran the notebook and tests myself.
