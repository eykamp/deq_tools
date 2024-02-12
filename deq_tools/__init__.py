 # Copyright 2018-2023, Chris Eykamp

# MIT License

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# pyright: strict

from typing import Optional, List, Dict, Any
import requests                                                 # pip install requests
from pydantic import BaseModel, Field, validator                # pip install pydantic      # type: ignore
from tenacity import retry, stop_after_attempt, wait_fixed      # pip install tenacity
from datetime import datetime as dt


# DEQ data display: https://aqi.oregon.gov

STATION_URL = "https://aqiapi.oregon.gov/v1/envista/regions"        # Retrieves station data
DATA_URL = "https://aqiapi.oregon.gov/v1/envista/stations"          # Retrieves data from a station

# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6IndlYiIsIm5iZiI6MTcwNTk4NTM3OSwiZXhwIjoxNzA1OTg4OTc5LCJpYXQiOjE3MDU5ODUzNzl9.tCT1fh8pOaFAnRwM3PE8GNx4LzFDS-XMmOTK2dKsc2E
# Data models derived from https://app.quicktype.io

class Location(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Monitor(BaseModel):
    channel_id: Optional[int] = Field(None, alias="channelId")
    name: Optional[str] = None
    alias: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    type_id: Optional[int] = Field(None, alias="typeId")
    pollutant_id: Optional[int] = Field(None, alias="pollutantId")
    units: Optional[str] = None
    unit_id: Optional[int] = Field(None, alias="unitID")
    map_view: Optional[bool] = Field(None, alias="mapView")
    is_index: Optional[bool] = Field(None, alias="isIndex")
    pollutant_category: Optional[int] = Field(None, alias="PollutantCategory")
    numeric_format: Optional[str] = Field(None, alias="NumericFormat")
    low_range: Optional[int] = Field(None, alias="LowRange")
    high_range: Optional[int] = Field(None, alias="HighRange")
    state: Optional[int] = None
    pct_valid: Optional[int] = Field(None, alias="PctValid")
    monitor_title: Optional[str] = Field(None, alias="MonitorTitle")
    mon_start_date: Optional[dt] = Field(None, alias="MON_StartDate")       # First date with data
    mon_end_date: Optional[dt] = Field(None, alias="MON_EndDate")           # Last date with data


    @staticmethod
    def interpret_date(value: str) -> dt:
        return dt.strptime(value, "%m/%d/%Y %I:%M:%S %p")     # "12/31/9999 11:59:59 PM"

    @validator("mon_start_date", pre=True)
    def parse_dt1(cls, value: str):
        return cls.interpret_date(value)

    @validator("mon_end_date", pre=True)
    def parse_dt2(cls, value: str):
        return cls.interpret_date(value)


class Station(BaseModel):
    station_id: int = Field(None, alias="stationId")
    stations_tag: Optional[str] = Field(None, alias="stationsTag")
    height: Optional[int] = None
    name: Optional[str] = None
    short_name: Optional[str] = Field(None, alias="shortName")
    location: Optional[Location] = None
    timebase: Optional[int] = None
    active: Optional[bool] = None
    owner: Optional[str] = None
    owner_id: Optional[int] = Field(None, alias="ownerId")
    region_id: Optional[int] = Field(None, alias="regionId")
    monitors: Optional[List[Monitor]] = None
    station_target: Optional[str] = Field(None, alias="StationTarget")
    target_id: Optional[int] = Field(None, alias="TargetId")
    county: Optional[str] = Field(None, alias="County")
    city: Optional[str] = None
    address: Optional[str] = None
    time_bases: Optional[List[int]] = Field(None, alias="timeBases")
    additional_timebases: Optional[str] = Field(None, alias="additionalTimebases")
    is_non_continuous: Optional[str] = Field(None, alias="isNonContinuous")
    map_view: Optional[bool] = Field(None, alias="mapView")
    aqi_view: Optional[bool] = Field(None, alias="aqiView")
    mobile: Optional[bool] = None
    aqscode: Optional[str] = Field(None, alias="AQSCODE")


class Region(BaseModel):
    region_id: Optional[int] = Field(None, alias="regionId")
    name: Optional[str] = None
    stations: List[Station]


class Channel(BaseModel):
    value_date: Optional[Any] = None    # I've never seen a value for this
    status: Optional[int] = None
    value: Optional[float] = None
    valid: Optional[bool] = None
    id: Optional[int] = None
    units: Optional[str] = None
    name: Optional[str] = None


class StationDatum(BaseModel):
    datetime: Optional[dt] = None
    channels: List[Channel] = []


class MonitorData(BaseModel):
    data: List[StationDatum]


"""
station_id: See bottom of this file for a list of valid station ids
from_timestamp, to_timestamp: specify in ISO datetime format: YYYY/MM/DDTHH:MM (e.g. "2018/05/03T00:00")
resolution: 60 for hourly data, 1440 for daily averages.  Higher resolutions such as 1 and 5 are available for some stations.
agg_method: These work (not sure what the difference is): Average, RunningAverage
percent_valid: No idea what this parameter does.
"""
def get_data(station_id: int, from_timestamp: dt, to_timestamp: dt, channels: Optional[List[int]] = None, resolution: int = 60, agg_method: str = "Average", percent_valid: int = 75) -> MonitorData:
    params = {
        "filterChannels": ",".join([str(s) for s in channels]) if channels else "",
        "from": from_timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
        "to": to_timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
        "fromTimebase": resolution,
        "toTimebase": resolution,
        "precentValid": percent_valid,
        "timeBeginning": False,
        "useBackWard": True,
        "unitConversion": False,
        "includeSummary": False,
        "onlySummary": False,
    }

    req = get(f"{DATA_URL}/{station_id}/{agg_method}", params=params, headers=get_request_headers())

    return MonitorData(**req.json())


def get_request_headers():
    headers = get_standard_headers()

    headers["Authorization"] = f"ApiToken {get_auth_token()}"
    return headers


def get_standard_headers():
    return {"Content-Type": "application/json; charset=UTF-8"}


def get_auth_token():
    return requests.post(
        url="https://aqi.oregon.gov/Account/GetApiToken",
        headers=get_standard_headers(),
        json={"userName": "web"},
    ).json()


def get_station_data() -> List[Region]:
    regions: List[Region] = []
    for region_json in get(STATION_URL, headers=get_request_headers()).json():        # Should work with no headers as well
        region = Region(**region_json)
        if region.region_id and region.name:
                regions.append(region)

    return regions


def get_station_names() -> Dict[int, str]:
    station_names: Dict[int, str] = {}

    station_data = get_station_data()
    for region in station_data:
        for station in region.stations:
            if station.station_id is not None and station.name is not None:
                station_names[station.station_id] = station.name

    return station_names


# These fail a lot, so we'll try tenacity
@retry(stop=stop_after_attempt(10), wait=wait_fixed(10), reraise=True)
def post(*args: Any, **kwargs: Any) -> requests.Response:
    req = requests.post(*args, **kwargs)
    req.raise_for_status()
    return req


@retry(stop=stop_after_attempt(10), wait=wait_fixed(10), reraise=True)
def get(*args: Any, **kwargs: Any) -> requests.Response:
    req = requests.get(*args, **kwargs)
    req.raise_for_status()
    return req



"""
To get a current list of stations, print the output of deq_tools.get_station_names(); use the
station_id in the left column when calling get_data()

These station ids were current as of November 2023:
1: 'Tualatin Bradbury Court'
2: 'Portland SE Lafayette'
6: 'Portland Jefferson HS'
7: 'Sauvie Island'
8: 'Beaverton Highland Park'
9: 'Hillsboro Hare Field'
10: 'Carus Spangler Road'
11: 'Salem State Hospital'
12: 'Turner Cascade Junior HS'
13: 'Lyons Marilynn School'
14: 'Albany Calapooia School'
15: 'Sweet Home Fire Department'
19: 'Grants Pass Parkside School'
20: 'Medford TV'
22: 'Provolt Seed Orchard'
23: 'Shady Cove School'
24: 'Talent'
26: 'Klamath Falls Peterson School'
27: 'Lakeview Center and M'
28: 'Bend Pump Station'
29: 'Multorpor'
30: 'Baker City Forest Service'
31: 'Enterprise Forest Service'
32: 'La Grande Hall and N'
33: 'Pendleton McKay Creek'
34: 'The Dalles Cherry Heights School'
35: 'Cove City Hall'
37: 'Hermiston Municipal Airport'
39: 'Bend Road Department'
40: 'Madras Westside Elementary'
41: 'Prineville Davidson Park'
42: 'Burns Washington Street'
43: 'Detroit Lake Forest Service'
44: 'Silverton James and Western'
45: 'Mill City'
46: 'John Day Dayton Street'
47: 'Sisters Forest Service'
48: 'Cave Junction Forest Service'
49: 'Medford Welch and Jackson'
50: 'Ashland Fire Department'
52: 'Portland Humboldt School'
56: 'Eugene Amazon Park'
57: 'Cottage Grove City Shops'
58: 'Springfield City Hall'
59: 'Eugene Saginaw'
60: 'Oakridge'
61: 'Eugene Wilkes Drive'
64: 'Portland Cully Helensview'
65: 'Eugene Highway 99'
67: 'Hillsboro Hare Field Sensor'
68: 'Hillsboro Hare Field Meteorological'
69: 'Forest Grove Pacific University'
75: 'Florence Forestry Department'
78: 'Portland Humboldt Sensors'
81: 'Portland SE12th and Salmon'
82: 'Chiloquin Duke Drive'
83: 'Brookings CPFA'
85: 'Redmond High School'
88: 'Coos Bay Marshfield HS'
89: 'Bend NE 8th & Emerson'
90: 'Roseburg Fire Dept'
105: 'La Pine Rural Fire Dept 103'
106: 'Bend NE 8th & Emerson Sensors'
107: 'Gresham Centennial High School'
109: 'Dallas LaCreole Middle School'
110: 'Ontario May Roberts Elementary School'
111: 'Hood River West Side Fire Department'
112: 'Corvallis EPA Office'
113: 'Estacada Clackamas River Sc'
114: 'Portland Roosevelt High School'
115: 'Portland Lane Middle School'
117: 'Portland Lincoln High School'
118: 'Portland McDaniel High School'
120: 'Bend Ponderosa Elementary School'
121: 'Bend Pine Ridge Elementary School'
122: 'Sunriver Three Rivers Elementary School'
123: 'Salem Chemeketa Community College'
124: 'Woodburn Chemeketa Community College'
125: 'Toledo NE HWY20 & NW A St'
126: 'Tillamook Jr High School'
133: 'McMinnville High School'
140: 'Medford Jackson Park'
142: 'Sisters Forest Service SensOR'

"""
