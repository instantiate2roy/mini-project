import requests
import time
from .http_request_exception import HttpRequestException
import pandas
from abc import ABC, abstractmethod

class WeatherForecast(ABC):
    """
    weather forecast class
    """
    #define my end-points
    geo_code_uri_end_points: str = "https://geocoding-api.open-meteo.com/v1/search"

    def __init__(self, email:str):
        self.email=email
        
    def geocode(self, location: str, time_out: float = 10) -> dict:
        """
        Method to get geocode details
        """
        base_url = self.geo_code_uri_end_points
        params = {"name": location, "count": 10, "language": 'en', "format": 'json'}
        
        results = self.make_request(base_url, params, {}, time_out).json().get("results", [])
                
        if not results:
            raise ValueError(f"No results found for {location!r}")
        
        #handle multi-value geocode/ambiguous names
        return self.__process_multi_result_geocode(results, location)

    @abstractmethod
    def get_forecast(self, lat: float, lon: float, n_days: int = 7, time_zone: str = 'auto',
                     time_out: float = 10) -> dict:
        """
        Absract Get forcast info for a location for n_days
        """
        pass

    @abstractmethod
    def forecast_to_dataframe(self, forecast: dict) -> pandas.DataFrame:
        """
        map forecast JSON into a readable pandas dataframe.
        """
        pass

    def make_request(self, uri: str, params: dict, headers: dict, time_out: float = 10,
                       max_retries: int = 3, initial_delay: float = 1.0, 
                       max_delay: float = 10.0) -> requests.Response:
        """
        Methed to handle http requests
        """
        resp = None
        for attempt in range(1, max_retries + 2):
            try:
                resp = requests.get(uri, params=params, headers=headers, timeout=time_out)
                resp.raise_for_status()
                break

            except requests.HTTPError as e:
                status = e.response.status_code
                if status < 500:
                    raise HttpRequestException(uri, attempt, f"HTTP {status} {e.response.reason}") from e
                error = e
                reason = f"HTTP {status} {e.response.reason}"
            except  requests.Timeout as e:
                error = e
                reason = f"timed out after {time_out} s"
            except requests.ConnectionError as e:
                error = e
                reason = f"could not connect ({e})"     
                            
            if attempt <= max_retries:
                #Raise the retry window on subsequent failures
                time.sleep(min(initial_delay * 2 ** (attempt - 1), max_delay))
        if not resp:
            raise HttpRequestException(uri, attempt, reason ) from error
        
        return resp

    def __process_multi_result_geocode(self, results: list[dict], location: str) -> dict:
        """
        Handle  multi record responses for geocode info
        """
        final_results = results[0]
        
        #if more than 1 record, let the user choose
        if len(results) > 1:
            lines = [f"Found {len(results)} matches for {location!r}:"]
            for i, res in enumerate(results, 1):
                label = ", ".join(p for p in [res['name'], res.get('admin1'), res.get('country')] if p)
                lines.append(f"  {i}. {label}")
            lines.append(f"Choose a location (1-{len(results)}): ")
            prompt = "\n".join(lines)
        
            while True:
                choice = input(prompt)
                if choice.isdigit() and 1 <= int(choice) <= len(results):
                    final_results = results[int(choice) - 1]
                    break
                print("Choose a location number from the list.")

        return final_results