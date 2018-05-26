Install with pip:<br>
`pip install deq-tools`

deq_tools is a limited functionality Python library for accessing Oregon DEQ Air Quality data with a Python script.

Usage:
```python
import deq_tools

print(deq_tools.get_station_names())    # Dump a list of names of stations where data may be available
print(deq_tools.get_station_data())     # Dump all station info, including data available for each station
    
station_id = 2                          # Get this value from get_station_names()
from_ts = "2018/05/03T00:00"            # ISO datetime format: YYYY/MM/DDTHH:MM
to_ts = "2018/05/10T23:59"

print(deq_tools.get_data(station_id, from_ts, to_ts))   # Get the data
```    
    
In addition to the required positional parameters shown above, `get_deq_data()` also takes these optional named parameters: 
<dl>    
  <dt>resolution:</dt><dd>Default = 60. 60 for hourly data, 1440 for daily values.  Higher resolutions don't work, sorry, but lower-resolutions, such as 120, 180, 480, 720 will.  </dd>
    <dt>agg_method:</dt><dd>Default = "Average". These will <i>probably</i> all work: Average, MinAverage, MaxAverage, RunningAverage, MinRunningAverage, MaxRunningAverage, RunningForword, MinRunningForword, MaxRunningForword.  </dd>
</dl>
