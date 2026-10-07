import pandas
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from IPython.display import display, Markdown
 
class WeatherReport:
    """
    Class for generating, displaying table and chart for a daily forecast DataFrame
    """
 
    date_format = "%a %d %b"  # example Wed 07 Oct"
 
    def __init__(self, data_frame: pandas.DataFrame, place_name: str):
        """
        constructor to inject external dependencies

        Store the forecast and look up its columns and units once,
        so every part of the report uses the same names.

        """
        self.data_frame = data_frame
        self.place_name = place_name
 
        self.t_max = self._find_column("Max temperature")
        self.t_min = self._find_column("Min temperature")
        self.rain = self._find_column("Precipitation")
        self.wind = self._find_column("Max wind speed")
 
        self.temp_unit = self._unit_of(self.t_max)
        self.rain_unit = self._unit_of(self.rain)
        self.wind_unit = self._unit_of(self.wind)
 
    
    def _find_column(self, start):
        """
        Find a column by the start of its name, so units like (°C) or (°F) don't matter.
        """
        return next(c for c in self.data_frame.columns if c.startswith(start))
 
    @staticmethod
    def _unit_of(column):
        """
        Get the unit from a column name like 'Max temperature (°C)'.
        """
        return column.split("(")[-1].rstrip(")")
 
    def _day(self, date):
        """
        Format a date for display, e.g. 'Wed 07 Oct'.
        """
        return date.strftime(self.date_format)
 
    def show_summary(self):
        """
        Show a short summary of the forecast as a table.
        """
        data_frame = self.data_frame
        hottest = data_frame[self.t_max].idxmax()
        coldest = data_frame[self.t_max].idxmin()   # lowest daytime high
        coolest = data_frame[self.t_min].idxmin()
        wettest = data_frame[self.rain].idxmax()
        driest = data_frame[self.rain].idxmin()
        windiest = data_frame[self.wind].idxmax()
        rainy_days = (data_frame[self.rain] >= 1).sum()
        total_days = len(data_frame)

        # (measure, day, value) for each row of the table
        rows = [
            ("Average daytime high", "-", f"{data_frame[self.t_max].mean():.1f} {self.temp_unit}"),
            ("Average night-time low", "-", f"{data_frame[self.t_min].mean():.1f} {self.temp_unit}"),
            ("Warmest day", self._day(hottest), f"{data_frame.loc[hottest, self.t_max]} {self.temp_unit}"),
            ("Coldest day", self._day(coldest), f"{data_frame.loc[coldest, self.t_max]} {self.temp_unit}"),
            ("Coolest night", self._day(coolest), f"{data_frame.loc[coolest, self.t_min]} {self.temp_unit}"),
            ("Total rain", "-", f"{data_frame[self.rain].sum():.1f} {self.rain_unit}"),
            ("Rainy days (1 mm or more)", "-", f"{rainy_days} of {total_days}"),
            ("Wettest day", self._day(wettest), f"{data_frame.loc[wettest, self.rain]} {self.rain_unit}"),
            ("Driest day", self._day(driest), f"{data_frame.loc[driest, self.rain]} {self.rain_unit}"),
            ("Windiest day", self._day(windiest), f"{data_frame.loc[windiest, self.wind]} {self.wind_unit}"),
        ]
        if "Weather" in data_frame:
            rows.append(("Most common conditions", "-", data_frame["Weather"].mode()[0]))

        # build the Markdown table
        lines = [
            f"## {total_days}-day forecast for {self.place_name}",
            f"**From {data_frame.index[0]:%d %b} To {data_frame.index[-1]:%d %b %Y}**",
            "",
            "| Measure | Day | Value |",
            "|---|---|---|",
            *(f"| {measure} | {day} | {value} |" for measure, day, value in rows),
        ]

        display(Markdown("\n".join(lines)))
 
    def show_table(self):
        """
        Show the forecast table.
        """
        table = self.data_frame.drop(columns="Weather code", errors="ignore").copy()
        table.index = table.index.strftime(self.date_format)
 
        numbers = [self.t_max, self.t_min, self.rain, self.wind]
        one_decimal = {col: "{:.1f}" for col in numbers}
 
        styled = (
            table.style
            .format(one_decimal)
            .background_gradient(subset=[self.t_max, self.t_min], cmap="coolwarm")
            .bar(subset=[self.rain], color="#9ecae1")
            .set_caption(f"Daily forecast for {self.place_name}")
        )
        display(styled)
 
    def plot(self):
        """
        Plot the temperature range as a band with precipitation as bars.
        """
        data_frame = self.data_frame
        fig, ax_temp = plt.subplots(figsize=(10, 5))
        # second y-axis on the right for rain
        ax_rain = ax_temp.twinx()  
 
        # precipitation bar
        ax_rain.bar(data_frame.index, data_frame[self.rain], width=0.6, color="tab:blue", alpha=0.25, label="Precipitation")
        ax_rain.set_ylabel(self.rain)
        ax_rain.set_ylim(0, max(data_frame[self.rain].max() * 1.5, 1))  # add top padding, leave room above the bars
 
        # temperature band and lines
        ax_temp.fill_between(data_frame.index, data_frame[self.t_min], data_frame[self.t_max], color="tab:orange", alpha=0.2, label="Temperature range")
        ax_temp.plot(data_frame.index, data_frame[self.t_max], marker="o", color="tab:red", label="Max temperature")
        ax_temp.plot(data_frame.index, data_frame[self.t_min], marker="o", color="tab:blue", label="Min temperature")
        ax_temp.set_ylabel(f"Temperature ({self.temp_unit})")
 
        # draw the temperature lines on top of the rain bars
        ax_temp.set_zorder(ax_rain.get_zorder() + 1)
        ax_temp.patch.set_visible(False)
 
        # one tick per day, e.g. "Wed 07 Oct"
        ax_temp.xaxis.set_major_locator(mdates.DayLocator())
        ax_temp.xaxis.set_major_formatter(mdates.DateFormatter(self.date_format))
        fig.autofmt_xdate()
 
        # one legend for both axes
        temp_handles, temp_labels = ax_temp.get_legend_handles_labels()
        rain_handles, rain_labels = ax_rain.get_legend_handles_labels()
        ax_temp.legend(temp_handles + rain_handles, temp_labels + rain_labels,
                       loc="upper left", fontsize=9)
 
        ax_temp.set_title(f"Temperature range and precipitation: {self.place_name}")
        ax_temp.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.show()
 
    def show(self):
        """
        Show the summary, table and chart.
        """
        self.show_summary()
        self.show_table()
        self.plot()