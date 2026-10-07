from .weather_forecast import WeatherForecast
import pandas

class OpenMeteo(WeatherForecast):
    """
    Open meteo-forecasting class
    """
    forecast_end_point = "https://api.open-meteo.com/v1/forecast"
    
    codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Depositing rime fog", 
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle", 56: "Light freezing drizzle", 57: "Dense freezing drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 66: "Light freezing rain", 67: "Heavy freezing rain", 
        71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall", 77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers", 
        82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers", 95: "Thunderstorm", 96: "Thunderstorm with slight hail", 
        99: "Thunderstorm with heavy hail",
        }

    fields = {
        "time": "Date",
        "weather_code": "Weather code",
        "temperature_2m_max": "Max temperature",
        "temperature_2m_min": "Min temperature",
        "precipitation_sum": "Precipitation",
        "wind_speed_10m_max": "Max wind speed",
    }

    def get_forecast(self, lat:float, lon:float, n_days:int = 7, time_zone ='auto', time_out = 10):
        """
        Get forcast info for a location for n_days
        """
        #consider api's forecast limit, this api can only forecast 16 ahead and cant do less than 1 day
        if not 1 <= n_days <= 16:
            raise ValueError("days must be between 1 and 16")
        
        base_url = self.forecast_end_point
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "timezone": time_zone,  # dates follow the location's local time
            "forecast_days": n_days,
        }
        return self.make_request(base_url, params, {}, time_out).json()
    
    def forecast_to_dataframe(self, forecast):
        """
        map forecast JSON into a readable pandas dataframe.
        """
        daily = forecast["daily"]
        units = forecast["daily_units"]
    
        df = pandas.DataFrame(daily)
        df["time"] = pandas.to_datetime(df["time"])
    
        # add a text description right after the numeric weather code
        if "weather_code" in df:
            description = df["weather_code"].map(self.codes).fillna("Unknown")
            df.insert(df.columns.get_loc("weather_code") + 1, "Weather", description)
    
        # rename columns and add units
        new_names = {}
        for col in df.columns:
            name = self.fields.get(col, col)
            if col not in ("time", "weather_code") and units.get(col):
                name = f"{name} ({units[col]})"
            new_names[col] = name
    
        return df.rename(columns=new_names).set_index("Date")   