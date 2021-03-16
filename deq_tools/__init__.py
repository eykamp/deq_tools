# Copyright 2018-2020, Chris Eykamp

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

import requests                                                 # pip install requests
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator                # pip install pydantic
from tenacity import retry, stop_after_attempt, wait_fixed      # pip install tenacity
from datetime import datetime as dt, timedelta, timezone

STATION_URL = "https://oraqi.deq.state.or.us/ajax/getAllStationsWithoutFiltering"
DATA_URL = "https://oraqi.deq.state.or.us/report/GetMultiStationReportData"

REQUEST_HEADERS = {"Content-Type": "application/json; charset=UTF-8"}


class Channel(BaseModel):
    display_name: str = Field(alias="DisplayName")
    id: int
    name: str
    alias: Optional[str]
    value: float
    status: int
    valid: bool
    description: Optional[str]
    value_date: Optional[str]
    units: str

class StationRecord(BaseModel):
    datetime: dt
    channels: List[Channel]

    @validator("datetime", pre=True)        # pre lets us modify the incoming value before it's parsed by pydantic
    def fix_deq_date(cls, val: str):
        """
        Datetimes reported by DEQ have a reported UTC offset of -05:00 but are actually -08:00.
        First, we'll verify that the dates are still broken in the way we expect them to be;
        Second, we'll fix them before importing.  This *should* work during both PST and PDT.

        Note on DEQ website (in footer of interactive reports page):
        Data on this site is presented in Standard Time at the time the measurement ended. There
        is no adjustment for Daylight Saving Time during its use from March to November.
        PST is UTC - 8 hours

        Further note that during DST, the adjusted times will not align with what is shown on the website
        because website times are in PST, but adjusted times may appear in PDT when converted from
        epoch time.
        """
        # if "-05:00" in val:      # Confirm data is still being reported with utcoffset -5 hours
        #     return val.replace("-05:00", "-08:00")
        if "-07:00"  in val or "-08:00" in val:
            return val
        raise Exception(f"Unexpected timezone in datetime: {val}")

"""
station_id: See bottom of this file for a list of valid station ides
from_timestamp, to_timestamp: specify in ISO datetime format: YYYY/MM/DDTHH:MM (e.g. "2018/05/03T00:00")
resolution: 60 for hourly data, 1440 for daily averages.  Higher resolutions don't work, sorry, but lower-resolutions, such as 120, 180, 480, 720 will.
agg_method: These will *probably* all work: Average, MinAverage, MaxAverage, RunningAverage, MinRunningAverage, MaxRunningAverage, RunningForword, MinRunningForword, MaxRunningForword
"""
def get_data(station_id: int, from_timestamp: dt, to_timestamp: dt, resolution: int = 60, agg_method: str = "Average") -> List[StationRecord]:
    # count = 99999               # This should be greater than the number of reporting periods in the data range specified above

    # params = "Sid=" + str(station_id) + "&FDate=" + from_timestamp + "&TDate=" + to_timestamp + "&TB=60&ToTB=" + str(resolution) + "&ReportType=" + \
    #     agg_method + "&period=Custom_Date&first=true&take=" + str(count) + "&skip=0&page=1&pageSize=" + str(count)


    channel_list: List[int] = list()

    stations = get_station_data()
    for station in stations:
        if station["serialCode"] == station_id:
            for monitor in station["monitors"]:
                channel_list.append(monitor["channel"])
            break


    payload = {
        "monitorChannelsByStationId": {
            str(station_id): channel_list
        },
        "reportName": "multi Station report",
        "startDateAbsolute": from_timestamp.strftime("%Y/%m/%dT%H:%MZ"),        # UTC -- site seems timezone-aware
        "endDateAbsolute": to_timestamp.strftime("%Y/%m/%dT%H:%MZ"),
        "startDate": from_timestamp.strftime("%Y/%m/%dT%H:%MZ"),
        "endDate": to_timestamp.strftime("%Y/%m/%dT%H:%MZ"),
        "reportType": agg_method,
        "fromTb": resolution,
        "toTb": resolution,
        "monitorChannelsByStationId[0].Key": str(station_id),
        "monitorChannelsByStationId[0].Value": channel_list
    }

    req = post(DATA_URL, headers=REQUEST_HEADERS, data=json.dumps(payload))

    req.raise_for_status()

    records = req.json()[0]["data"]     # type: ignore

    all_records: List[StationRecord] = list()

    for record in records:
        all_records.append(StationRecord(datetime=record["datetime"], channels=record["channels"]))

    # This need not remain here permanently, but for now let's verify the data arrived in chronological order.
    # If this ever fails, we'll sort.
    for i, record in enumerate(all_records[1:]):
        assert all_records[i].datetime < record.datetime

    return all_records


# These fail a lot, so we'll try tenacity
@retry(stop=stop_after_attempt(10), wait=wait_fixed(10), reraise=True)
def post(*args: Any, **kwargs: Any) -> requests.Response:
    req = requests.post(*args, **kwargs)                        # type: ignore
    req.raise_for_status()
    return req


@retry(stop=stop_after_attempt(10), wait=wait_fixed(10), reraise=True)
def get(*args: Any, **kwargs: Any) -> requests.Response:
    req = requests.get(*args, **kwargs)                         # type: ignore
    req.raise_for_status()
    return req


def get_station_data() -> List[Dict[str, Any]]:
    return post(STATION_URL, headers=REQUEST_HEADERS).json()    # type: ignore


def get_station_names() -> Dict[int, str]:
    stations_names = {}

    stations = get_station_data()
    for station in stations:
        stations_names[station["serialCode"]] = station["name"]

    return stations_names


"""
To get a current list of stations, print the output of deq_tools.get_station_names()
These station ids were current as of Sept 2020:
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
    16: 'Corvallis Circle Blvd'
    17: 'Roseburg Garden Valley'
    19: 'Grants Pass Parkside School
    20: 'Medford TV'
    22: 'Provolt Seed Orchard'
    23: 'Shady Cove School'
    24: 'Talent'
    26: 'Klamath Falls Peterson School'
    27: 'Lakeview Center and M'
    28: 'Bend Pump Station'
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
    44: 'Silverton James and Western'
    46: 'John Day Dayton Street'
    47: 'Sisters Forest Service'
    48: 'Cave Junction Forest Service'
    49: 'Medford Welch and Jackson'
    50: 'Ashland Fire Department'
    56: 'Eugene Amazon Park'
    57: 'Cottage Grove City Shops'
    58: 'Springfield City Hall'
    59: 'Eugene Saginaw'
    60: 'Oakridge'
    61: 'Eugene Wilkes Drive'
    64: 'Portland Cully Helensview'
    65: 'Eugene Highway 99'
    67: 'Hillsboro Hare Field Sensor'
    68: 'Hillsboro Hare Field Meteorology'
    69: 'Forest Grove Pacific University'
    75: 'Florence Forestry Department'
    78: 'Portland Humboldt Sensors'
    82: 'Chiloquin Duke Drive'
    85: 'Redmond High School'
    88: 'Coos Bay Marshfield HS
    90: 'Roseburg Fire Dept'
"""
