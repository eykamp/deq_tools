# Copyright 2018, Chris Eykamp

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

import requests
import json
import re


station_url = "https://oraqi.deq.state.or.us/report/RegionReportTable"
data_url = "https://oraqi.deq.state.or.us/report/stationReportTable"

"""
station_id: See bottom of this file for a list of valid station ides
from_timestamp, to_timestamp: specify in ISO datetime format: YYYY/MM/DDTHH:MM (e.g. "2018/05/03T00:00")
resolution: 60 for hourly data, 1440 for daily averages.  Higher resolutions don't work, sorry, but lower-resolutions, such as 120, 180, 480, 720 will.
agg_method: These will *probably* all work: Average, MinAverage, MaxAverage, RunningAverage, MinRunningAverage, MaxRunningAverage, RunningForword, MinRunningForword, MaxRunningForword
"""


def get_data(station_id, from_timestamp, to_timestamp, resolution=60, agg_method="Average"):
    count = 99999               # This should be greater than the number of reporting periods in the data range specified above

    params = "Sid=" + str(station_id) + "&FDate=" + from_timestamp + "&TDate=" + to_timestamp + "&TB=60&ToTB=" + str(resolution) + "&ReportType=" + \
        agg_method + "&period=Custom_Date&first=true&take=" + str(count) + "&skip=0&page=1&pageSize=" + str(count)

    req = requests.get(data_url + "?" + params)
    (status, reason) = (req.status_code, req.reason)

    json_response = json.loads(req.text)

    response_data = json_response.get("Data")
    field_descr = json_response.get("ListDicUnits")

    if not field_descr or not response_data:
        # Something went wrong -- request probably came back empty
        raise Exception("Successfully able to connect to DEQ, but data came back without all the parts we need.  Response text: " + req.text)

    titles = {}
    units = {}

    for d in field_descr:
        name = d["field"]
        words = re.split('<br/>', d["title"])       # d["title"] ==> Wind Direction <br/>Deg
        titles[name] = words[0].strip()
        if len(words) > 1:
            units[name] = words[1].strip()
        else:
            units[name] = ""

    data = {}       # Restructured sensor data retrieved from DEQ

    for d in response_data:
        dt = d["datetime"]

        for key, val in d.items():
            if key != "datetime":
                # Remove missing values
                if val == "----":
                    continue

                if dt not in data:
                    data[dt] = {}

                data[dt][titles[key]] = val

    return data


def get_station_data():
    req = requests.get(station_url)
    return json.loads(req.text)["Data"]


def get_station_names():
    data = get_station_data()

    stations = {}

    for d in data:
        for r in d["stations"]:
            stations[r["stationId"]] = r["name"]

    return stations


'''
To get a current list of stations, print the output of deq_tools.get_station_names()
These station ids were current as of June 2020:
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
'''
