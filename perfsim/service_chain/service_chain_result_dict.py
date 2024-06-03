#  Copyright (C) 2020 Michel Gokan Khan
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#  This file is a part of the PerfSim project, which is now open source and available under the GPLv2.
#  Written by Michel Gokan Khan, February 2020

from __future__ import annotations

from typing import Union, TypedDict, Dict

from pandas import Interval

from perfsim import ServiceChainResultIterationDict


class ServiceChainResultDict(TypedDict):
    simulation_name: str
    estimated_cost: Union[int, float]
    total_requests: int
    successful_requests: int
    timeout_requests: int
    avg_latency: float
    throughput: Dict[Interval, int]
    arrival_times: ServiceChainResultIterationDict
    latencies: ServiceChainResultIterationDict
    completion_times: ServiceChainResultIterationDict
    traffic_types: ServiceChainResultIterationDict
