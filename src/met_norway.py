from .weather_forecast import WeatherForecast
import pandas
from collections import Counter
from collections.abc import Iterator
from zoneinfo import ZoneInfo

class MetNorway(WeatherForecast):
    """
    Met norway forecasting class
    """
    forecast_end_point: str = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
    
    unit_names: dict[str, str] = {"celsius": "°C", "fahrenheit": "°F"}
    
    met_symbols: dict[str, str] = {
        "clearsky": "Clear sky", "fair": "Fair", "partlycloudy": "Partly cloudy",
        "cloudy": "Cloudy", "fog": "Fog",
        "lightrain": "Light rain", "rain": "Rain", "heavyrain": "Heavy rain",
        "lightrainshowers": "Light rain showers", "rainshowers": "Rain showers",
        "heavyrainshowers": "Heavy rain showers",
        "lightrainandthunder": "Light rain and thunder", "rainandthunder": "Rain and thunder",
        "heavyrainandthunder": "Heavy rain and thunder",
        "lightrainshowersandthunder": "Light rain showers and thunder",
        "rainshowersandthunder": "Rain showers and thunder",
        "heavyrainshowersandthunder": "Heavy rain showers and thunder",
        "lightsleet": "Light sleet", "sleet": "Sleet", "heavysleet": "Heavy sleet",
        "lightsnow": "Light snow", "snow": "Snow", "heavysnow": "Heavy snow",
    }

    def get_forecast(self, lat: float, lon: float, n_days: int = 7, time_zone: str = 'UTC',
                     time_out: float = 10) -> dict:
        """
        Get forcast info for a location for n_days
        """
        #met norway limit for the forecast is 10 days
        if not 1 <= n_days <= 10:
            raise ValueError("days must be between 1 and 10")

        #met norway rejects coordinates with more than 4 decimals
        params = {"lat": round(lat, 4), "lon": round(lon, 4)}
        headers = {"User-Agent": f"weather-mini-project/1.0 ({self.email})"}
        forecast = self.make_request(self.forecast_end_point, params, headers, time_out).json()

        # MET has no daily values or time zone option, so keep what forecast_to_dataframe needs
        forecast["timezone"] = "UTC" if time_zone == "auto" else time_zone
        forecast["n_days"] = n_days
        return forecast

    def forecast_to_dataframe(self, forecast: dict) -> pandas.DataFrame:
        """
        Group MET's hourly and 6-hourly time steps into a daily pandas dataframe,
        using the same column names as the OpenMeteo class.
        """
        tz = ZoneInfo(forecast.get("timezone", "UTC"))
        units = forecast["properties"]["meta"]["units"]

        steps = pandas.DataFrame(
            self.__read_time_step(entry, tz) for entry in self.__without_overlaps(forecast)
        )

        daily = (
            steps.groupby("date")
            .agg(t_max=("temp", "max"), t_min=("temp", "min"),
                 rain=("rain", "sum"), wind=("wind", "max"),
                 weather=("symbol", self.__describe))
            .head(forecast.get("n_days", 7))
            .round(1)
        )

        temp_unit = self.unit_names.get(units.get("air_temperature"), units.get("air_temperature"))
        daily = daily.rename(columns={
            "t_max": f"Max temperature ({temp_unit})",
            "t_min": f"Min temperature ({temp_unit})",
            "rain": f"Precipitation ({units.get('precipitation_amount')})",
            "wind": f"Max wind speed ({units.get('wind_speed')})",
            "weather": "Weather",
        })
        daily.index = pandas.to_datetime(daily.index)
        daily.index.name = "Date"

        # same column order as OpenMeteo: weather first
        return daily[["Weather"] + [c for c in daily.columns if c != "Weather"]]

    def __without_overlaps(self, forecast: dict) -> Iterator[tuple[dict, dict | None]]:
        """
        met norway gives 1-hour periods for the first days, then 6-hour periods.
        """
        covered_until = None
        for entry in forecast["properties"]["timeseries"]:
            t = pandas.Timestamp(entry["time"])
            data = entry["data"]
            if "next_1_hours" in data:
                period = data["next_1_hours"]
                covered_until = t + pandas.Timedelta(hours=1)
            elif "next_6_hours" in data and (covered_until is None or t >= covered_until):
                period = data["next_6_hours"]
                covered_until = t + pandas.Timedelta(hours=6)
            else:
                period = None
            yield entry, period

    def __read_time_step(self, entry_and_period: tuple[dict, dict | None], tz: ZoneInfo) -> dict:
        """
        Pull the values for one time step, with its time converted to local time.
        """
        entry, period = entry_and_period
        details = entry["data"]["instant"]["details"]
        return {
            "date": pandas.Timestamp(entry["time"]).tz_convert(tz).date(),
            "temp": details.get("air_temperature"),
            "wind": details.get("wind_speed"),
            "rain": period["details"].get("precipitation_amount", 0.0) if period else 0.0,
            "symbol": period["summary"]["symbol_code"] if period else None,
        }

    def __describe(self, symbols: pandas.Series) -> str:
        """
        Most common weather symbol of the day, as readable text.
        """
        codes = [s.split("_")[0] for s in symbols.dropna()]  # "lightrain_day" -> "lightrain"
        if not codes:
            return "Unknown"
        most_common = Counter(codes).most_common(1)[0][0]
        return self.met_symbols.get(most_common, most_common)            