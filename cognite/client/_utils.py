# -*- coding: utf-8 -*-
"""Utilites for Cognite API SDK

This module provides helper methods and different utilities for the Cognite API Python SDK.

This module is protected and should not used by end-users.
"""
import datetime
import platform
import re
import sys
import time
from datetime import datetime, timezone
from typing import Callable, List

import cognite


def datetime_to_ms(dt):
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)


def round_to_nearest(x, base):
    return int(base * round(float(x) / base))


def granularity_to_ms(time_string):
    """Returns millisecond representation of granularity time string"""
    magnitude = int("".join([c for c in time_string if c.isdigit()]))
    unit = "".join([c for c in time_string if c.isalpha()])
    unit_in_ms = {
        "s": 1000,
        "second": 1000,
        "m": 60000,
        "minute": 60000,
        "h": 3600000,
        "hour": 3600000,
        "d": 86400000,
        "day": 86400000,
    }
    return magnitude * unit_in_ms[unit]


def get_aggregate_func_return_name(agg_func: str) -> str:
    agg_funcs = {
        "avg": "average",
        "average": "average",
        "count": "count",
        "continuousvariance": "continuousvariance",
        "cv": "continuousvariance",
        "discretevariance": "discretevariance",
        "dv": "discretevariance",
        "int": "interpolation",
        "interpolation": "interpolation",
        "max": "max",
        "min": "min",
        "step": "stepinterpolation",
        "stepinterpolation": "stepinterpolation",
        "sum": "sum",
        "totalvariation": "totalvariation",
        "tv": "totalvariation",
    }
    return agg_funcs.get(agg_func)


def _time_ago_to_ms(time_ago_string):
    """Returns millisecond representation of time-ago string"""
    if time_ago_string == "now":
        return 0
    pattern = r"(\d+)([a-z])-ago"
    res = re.match(pattern, str(time_ago_string))
    if res:
        magnitude = int(res.group(1))
        unit = res.group(2)
        unit_in_ms = {"s": 1000, "m": 60000, "h": 3600000, "d": 86400000, "w": 604800000}
        return magnitude * unit_in_ms[unit]
    return None


def interval_to_ms(start, end):
    """Returns the ms representation of start-end-interval whether it is time-ago, datetime or None."""
    time_now = int(round(time.time() * 1000))
    if isinstance(start, datetime):
        start = datetime_to_ms(start)
    elif isinstance(start, str):
        start = time_now - _time_ago_to_ms(start)
    elif start is None:
        start = time_now - _time_ago_to_ms("2w-ago")

    if isinstance(end, datetime):
        end = datetime_to_ms(end)
    elif isinstance(end, str):
        end = time_now - _time_ago_to_ms(end)
    elif end is None:
        end = time_now

    return start, end


class Bin:
    """
    Attributes:
        entries (List): List of entries.
        get_count (Callable): Callable function to get count.
    """

    def __init__(self, get_count):
        """
        Args:
            get_count: A function that will take an element and get the count of something in it.
        """
        self.entries = []
        self.get_count = get_count

    def add_item(self, item):
        self.entries.append(item)

    def sum(self):
        total = 0
        for elem in self.entries:
            total += self.get_count(elem)
        return total

    def show(self):
        return self.entries


def first_fit(list_items: List, max_size, get_count: Callable) -> List[List]:
    """Returns list of bins with input items inside."""

    # Sort the input list in decreasing order
    list_items = sorted(list_items, key=get_count, reverse=True)

    list_bins = [Bin(get_count=get_count)]

    for item in list_items:
        # Go through bins and try to allocate
        alloc_flag = False

        for bin in list_bins:
            if bin.sum() + get_count(item) <= max_size:
                bin.add_item(item)
                alloc_flag = True
                break

        # If item not allocated in bins in list, create new bin
        # and allocate it to it.
        if not alloc_flag:
            new_bin = Bin(get_count=get_count)
            new_bin.add_item(item)
            list_bins.append(new_bin)

    # Turn bins into list of items and return
    list_items = []
    for bin in list_bins:
        list_items.append(bin.show())

    return list_items


def to_camel_case(snake_case_string: str):
    components = snake_case_string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def to_snake_case(camel_case_string: str):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_case_string)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def get_user_agent():
    sdk_version = "CognitePythonSDK/{}".format(cognite.__version__)

    python_version = "{}/{} ({};{})".format(
        platform.python_implementation(), platform.python_version(), platform.python_build(), platform.python_compiler()
    )

    os_version_info = [platform.release(), platform.machine(), platform.architecture()[0]]
    os_version_info = [s for s in os_version_info if s]  # Ignore empty strings
    os_version_info = "-".join(os_version_info)
    operating_system = "{}/{}".format(platform.system(), os_version_info)

    return "{} {} {}".format(sdk_version, python_version, operating_system)
