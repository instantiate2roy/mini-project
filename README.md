# OOP with Python: Assignment 2 mini-projects

Mini-projects from Assignment 2 (Advent 2026). Each one has its own notebook, with the reusable classes in `src/` and pytest tests in `tests/`.

| Notebook | Mini-project |
|---|---|
| `project1_weather_forecast.ipynb` | 1. Fetching and displaying a weather forecast with Python web APIs: geocodes a place name, downloads a forecast from Open-Meteo and MET Norway, and shows it as a table, a summary and a chart |

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

1. Open the notebook from the project folder, so that `src` can be imported:

   ```bash
   jupyter notebook project1_weather_forecast.ipynb
   ```

2. Create a file called `.env` in the project folder with your own university email:

   ```
   MET_API_EMAIL=your.name@university.ac.ug
   ```

   MET Norway requires a contact email in the `User-Agent` header of every request, so it can reach you about your traffic. `.env` is listed in `.gitignore`, so the email is never committed.
3. Choose **Kernel > Restart Kernel and Run All Cells**. The notebook needs an internet connection. The configuration cell asks for a location, which is the only manual input. If a name matches several places (for example "Springfield"), you pick one from the list.

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
| `tests/test_weather_forecast.py` | pytest tests for parsing, geocoding, requests, retries and the report |
| `tests/data/` | Sample JSON used by the tests (see below) |

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

## Findings

### Mini-project 1: Weather forecast

- **urllib and requests:** both return the same geocoding result. requests needs less code, encodes the query and decodes the JSON itself, and catches every failure through one exception class.
- **Response details:** the geocoding API answers with status 200 and `Content-Type: application/json`; the response time is printed for each run.
- **Two sources, one table:** Open-Meteo returns daily values directly. MET Norway only returns hourly and 6-hourly time steps in UTC, so `MetNorway` converts them to local time, groups them into days, and uses only the hourly rain where both periods overlap. Its table then has the same columns as Open-Meteo's, apart from wind in m/s instead of km/h.
- **Robustness:** an invalid city raises a clear `ValueError`. An invalid latitude (999) gets HTTP 400, which is not retried. With no network (simulated), a tiny timeout or repeated 5xx server errors, the request is tried 4 times with delays of 1, 2 and 4 seconds, then fails with `HttpRequestException`.

The full report (data flow, licensing, reliability and privacy) is at the end of the notebook.

## AI-use declaration

I used AI tools while working on this project:

- **Claude (Anthropic):**
  - Building the tests (`tests/test_weather_forecast.py`), the sample JSON in `tests/data/`, and `pytest.ini`.
  - Drafting this README and `requirements.txt`.
  - The fake connectivity simulation: replacing `requests.get` with a version that raises `ConnectionError`, and `time.sleep` with a recorder, so the no-network case and the retry delays can be shown without a real outage.
  - Code review of my code for correctness.
  - Getting the API request and response formats and their documentation for Open-Meteo Geocoding, Open-Meteo Forecast and MET Norway Locationforecast 2.0.
  - How to use MET Norway Locationforecast 2.0: the required `User-Agent`, coordinates limited to 4 decimals, the `compact` response format, and its mix of hourly and 6-hourly time steps.
  - Adding type hints to the class methods and attributes.
  - The 1,000–1,500 word write-up.

I wrote the original code and analysis. I reviewed all AI-generated code and text, and ran the notebook and tests myself.
