from typing import List, Any, Dict

import pytest
import json as Json
from datetime import datetime, timedelta
from jycm.jycm import YouchamaJsonDiffer        # Finds diffs between json structs

import deq_tools
from deq_tools import Region


@pytest.fixture(scope="session")
def raw_data():
    # Put in a fixture so it will only get run once
    return deq_tools.get(deq_tools.STATION_URL, headers=deq_tools.REQUEST_HEADERS).json()


@pytest.fixture(scope="session")
def station_data():
    # Put in a fixture so it will only get run once
    return deq_tools.get_station_data()


def test_models_count(station_data: List[Region]):
    assert len(station_data) > 0


def test_models_match_json(raw_data: List[Dict[str, Any]], station_data: List[Region]):
    """ This test confirms we can parse the regions/stations data slug, and that our model matches what the DEQ is providing. """
    # Eliminate null records from the raw_data
    filtered_json: List[Dict[str, Any]] = []
    for r in raw_data:
        if r["regionId"] != 0:
            filtered_json.append(r)

    for i, fj in enumerate(filtered_json):
        model_json = Json.loads(station_data[i].model_dump_json(by_alias=True))

        ycm = YouchamaJsonDiffer(model_json, fj)

        diff: Dict[str, Any]
        for diff in ycm.get_diff()["value_changes"]:                                                                                                                                # type: ignore
            # Expected difference -- we convert height from DEQ-provided string to integer
            if diff["left_path"].endswith("->height") and int(diff["left"]) == int(diff["right"]):                                                                                  # type: ignore
                continue
            # Expected differences -- we interpret and reformat dates
            if diff["left_path"].endswith("->MON_StartDate") and datetime.strptime(diff["left"], "%Y-%m-%dT%H:%M:%S") == datetime.strptime(diff["right"], "%m/%d/%Y %I:%M:%S %p"):  # type: ignore
                continue
            if diff["left_path"].endswith("->MON_EndDate") and datetime.strptime(diff["left"], "%Y-%m-%dT%H:%M:%S") == datetime.strptime(diff["right"], "%m/%d/%Y %I:%M:%S %p"):    # type: ignore
                continue

            assert False, "Model differs from raw JSON in an unexpected way."


def test_get_data(station_data: List[Region]):
    station_id = station_data[0].stations[0].station_id

    assert deq_tools.get_data(station_id, datetime.now() - timedelta(days=10), datetime.now())
