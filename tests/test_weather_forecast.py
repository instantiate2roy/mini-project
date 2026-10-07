"""Offline tests for mini-project 1. Every response comes from the saved JSON in tests/data,
so no test touches the network."""
import copy
import json
from pathlib import Path

import pandas
import pytest
import requests

from src.http_request_exception import HttpRequestException
from src.met_norway import MetNorway
from src.open_meteo import OpenMeteo
from src.weather_report import WeatherReport

DATA = Path(__file__).parent / 'data'
EMAIL = 'student@example.ac.ug'      # placeholder contact for the User-Agent, never a real address


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text())


def fake_response(status: int = 200, body: dict | None = None) -> requests.Response:
    """A real requests.Response with a set status and JSON body, so raise_for_status() behaves normally."""
    response = requests.Response()
    response.status_code = status
    response.reason = {200: 'OK', 404: 'Not Found', 503: 'Service Unavailable'}.get(status, '')
    response.url = 'https://api.example.test'
    response._content = json.dumps(body or {}).encode()
    return response


@pytest.fixture
def fake_get(monkeypatch):
    """Replace requests.get with a recorder that returns (or raises) the given results in order.
    time.sleep is replaced too, so retries run instantly and their delays can be checked."""
    calls, sleeps = [], []

    def install(*results):
        queue = list(results)

        def get(url, params=None, headers=None, timeout=None):
            calls.append({'url': url, 'params': params, 'headers': headers, 'timeout': timeout})
            result = queue.pop(0) if len(queue) > 1 else queue[0]
            if isinstance(result, Exception):
                raise result
            return result

        monkeypatch.setattr('src.weather_forecast.requests.get', get)
        monkeypatch.setattr('src.weather_forecast.time.sleep', sleeps.append)
        return calls, sleeps

    return install


# Open-Meteo forecast parsing

def test_open_meteo_forecast_becomes_a_daily_table_with_units():
    table = OpenMeteo(EMAIL).forecast_to_dataframe(load('open_meteo_forecast_kampala.json'))
    assert len(table) == 7
    assert table.index.name == 'Date'
    assert pandas.api.types.is_datetime64_any_dtype(table.index)
    assert list(table.columns) == ['Weather code', 'Weather', 'Max temperature (°C)', 'Min temperature (°C)',
                                   'Precipitation (mm)', 'Max wind speed (km/h)']


def test_open_meteo_weather_codes_are_decoded():
    forecast = load('open_meteo_forecast_kampala.json')
    table = OpenMeteo(EMAIL).forecast_to_dataframe(forecast)
    for code, description in zip(forecast['daily']['weather_code'], table['Weather']):
        assert description == OpenMeteo.codes[code]


def test_unknown_weather_code_is_labelled_unknown():
    # Edge case: a code missing from the Open-Meteo table must not break the table
    forecast = copy.deepcopy(load('open_meteo_forecast_kampala.json'))
    forecast['daily']['weather_code'][0] = 999
    assert OpenMeteo(EMAIL).forecast_to_dataframe(forecast)['Weather'].iloc[0] == 'Unknown'


# MET Norway forecast parsing

def met_forecast(timezone: str = 'Africa/Kampala', n_days: int = 7) -> dict:
    forecast = load('met_norway_compact_kampala.json')
    forecast['timezone'], forecast['n_days'] = timezone, n_days   # added by MetNorway.get_forecast
    return forecast


def test_met_time_steps_are_grouped_into_local_days():
    table = MetNorway(EMAIL).forecast_to_dataframe(met_forecast())
    oct_9 = table.loc['2026-10-09']
    # 00:00 to 23:59 Kampala time (UTC+3): 0.2 + 0.3 + 0.0 hourly, then 1.0 + 2.0 + 0.5 + 0.0 six-hourly
    assert oct_9['Precipitation (mm)'] == pytest.approx(4.0)
    assert oct_9['Max temperature (°C)'] == 27.0
    assert oct_9['Min temperature (°C)'] == 16.8
    assert oct_9['Max wind speed (m/s)'] == 4.5
    assert oct_9['Weather'] == 'Light rain'


def test_met_hourly_rain_is_not_counted_twice():
    # The first two steps carry both next_1_hours (0.2, 0.3 mm) and next_6_hours (5.0, 4.0 mm); only the hourly values count
    table = MetNorway(EMAIL).forecast_to_dataframe(met_forecast(timezone='UTC'))
    assert table.loc['2026-10-08', 'Precipitation (mm)'] == pytest.approx(0.5)


def test_met_table_uses_the_open_meteo_column_names():
    # Same names as Open-Meteo, so WeatherReport works with both; MET has no weather code and reports wind in m/s
    met = MetNorway(EMAIL).forecast_to_dataframe(met_forecast())
    assert list(met.columns) == ['Weather', 'Max temperature (°C)', 'Min temperature (°C)',
                                 'Precipitation (mm)', 'Max wind speed (m/s)']


def test_met_table_is_cut_to_the_requested_days():
    assert len(MetNorway(EMAIL).forecast_to_dataframe(met_forecast(n_days=1))) == 1


# Geocoding

def test_geocode_returns_the_single_match(fake_get):
    fake_get(fake_response(body=load('geocode_kampala.json')))
    place = OpenMeteo(EMAIL).geocode('Kampala')
    assert (place['name'], place['latitude'], place['longitude']) == ('Kampala', 0.31628, 32.58219)


def test_geocode_with_no_results_raises(fake_get):
    # Edge case: Open-Meteo leaves out the 'results' key when nothing matches
    fake_get(fake_response(body=load('geocode_no_results.json')))
    with pytest.raises(ValueError, match='No results'):
        OpenMeteo(EMAIL).geocode('Xyzzyqwertyville')


def test_ambiguous_name_lists_the_candidates_and_reprompts(fake_get, monkeypatch):
    fake_get(fake_response(body=load('geocode_springfield.json')))
    answers, prompts = iter(['abc', '7', '2']), []
    monkeypatch.setattr('builtins.input', lambda prompt: prompts.append(prompt) or next(answers))

    place = OpenMeteo(EMAIL).geocode('Springfield')

    assert place['admin1'] == 'Illinois'
    assert len(prompts) == 3                      # 'abc' and '7' are rejected, '2' is accepted
    assert 'Springfield, Missouri, United States' in prompts[0]


# Forecast requests

@pytest.mark.parametrize('client, days', [(OpenMeteo(EMAIL), 0), (OpenMeteo(EMAIL), 17), (MetNorway(EMAIL), 11)])
def test_forecast_days_outside_the_api_limit_are_rejected(client, days):
    with pytest.raises(ValueError):
        client.get_forecast(0.3, 32.6, n_days=days)


def test_open_meteo_request_asks_for_the_daily_fields(fake_get):
    calls, _ = fake_get(fake_response(body=load('open_meteo_forecast_kampala.json')))
    OpenMeteo(EMAIL).get_forecast(0.31628, 32.58219, n_days=7, time_zone='Africa/Kampala')
    params = calls[0]['params']
    assert params['daily'] == 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max'
    assert (params['timezone'], params['forecast_days']) == ('Africa/Kampala', 7)


def test_met_request_identifies_the_caller_and_rounds_coordinates(fake_get):
    calls, _ = fake_get(fake_response(body=load('met_norway_compact_kampala.json')))
    forecast = MetNorway(EMAIL).get_forecast(0.316283, 32.582191, n_days=3, time_zone='auto')
    assert calls[0]['params'] == {'lat': 0.3163, 'lon': 32.5822}           # MET accepts at most 4 decimals
    assert EMAIL in calls[0]['headers']['User-Agent']
    assert (forecast['timezone'], forecast['n_days']) == ('UTC', 3)        # 'auto' falls back to UTC


# Retries and errors

def test_no_network_retries_with_backoff_then_raises(fake_get):
    calls, sleeps = fake_get(requests.ConnectionError('Network is unreachable'))
    with pytest.raises(HttpRequestException) as error:
        OpenMeteo(EMAIL).make_request('https://api.example.test', {}, {}, max_retries=3)
    assert len(calls) == 4                        # the first try and 3 retries
    assert sleeps == [1.0, 2.0, 4.0]              # the delay doubles each time
    assert isinstance(error.value.__cause__, requests.ConnectionError)


def test_backoff_delay_is_capped(fake_get):
    _, sleeps = fake_get(requests.ConnectionError('down'))
    with pytest.raises(HttpRequestException):
        OpenMeteo(EMAIL).make_request('https://api.example.test', {}, {}, max_retries=6, max_delay=10.0)
    assert sleeps == [1.0, 2.0, 4.0, 8.0, 10.0, 10.0]


def test_timeout_is_reported_clearly(fake_get):
    fake_get(requests.Timeout('read timed out'))
    with pytest.raises(HttpRequestException, match='timed out after 0.001 s'):
        OpenMeteo(EMAIL).make_request('https://api.example.test', {}, {}, time_out=0.001, max_retries=1)


def test_client_errors_are_not_retried(fake_get):
    calls, sleeps = fake_get(fake_response(404))
    with pytest.raises(HttpRequestException, match='HTTP 404'):
        OpenMeteo(EMAIL).make_request('https://api.example.test', {}, {})
    assert len(calls) == 1 and sleeps == []


def test_server_error_is_retried_until_it_succeeds(fake_get):
    calls, sleeps = fake_get(fake_response(503), fake_response(200, {'ok': True}))
    response = OpenMeteo(EMAIL).make_request('https://api.example.test', {}, {})
    assert response.json() == {'ok': True}
    assert len(calls) == 2 and sleeps == [1.0]


def test_server_error_on_every_attempt_raises_the_custom_exception(fake_get):
    calls, sleeps = fake_get(fake_response(503))
    with pytest.raises(HttpRequestException, match='after 4 attempt.*HTTP 503'):
        OpenMeteo(EMAIL).make_request('https://api.example.test', {}, {}, max_retries=3)
    assert len(calls) == 4 and sleeps == [1.0, 2.0, 4.0]


def test_custom_exception_message_names_the_url_and_attempts():
    error = HttpRequestException('https://api.example.test', 4, 'could not connect')
    assert str(error) == ('Request Failed: Connection to https://api.example.test failed after 4 attempt(s): '
                          'could not connect')


# Report

@pytest.mark.parametrize('table, wind_unit', [
    (lambda: OpenMeteo(EMAIL).forecast_to_dataframe(load('open_meteo_forecast_kampala.json')), 'km/h'),
    (lambda: MetNorway(EMAIL).forecast_to_dataframe(met_forecast()), 'm/s'),
])
def test_report_finds_columns_and_units_from_either_source(table, wind_unit):
    report = WeatherReport(table(), 'Kampala')
    assert (report.temp_unit, report.rain_unit, report.wind_unit) == ('°C', 'mm', wind_unit)
    assert report.rain == 'Precipitation (mm)'
