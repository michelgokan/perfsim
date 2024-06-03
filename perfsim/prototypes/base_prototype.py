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

from abc import ABC
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from perfsim import SimulationScenarioManager


class BasePrototype(ABC):
    @staticmethod
    def get_prototypes(subject: Any, key: str, attribute: str, conf: Dict, existing_sm: 'SimulationScenarioManager'):
        if key in conf:
            return subject.from_config(conf=conf)
        elif existing_sm is not None:
            return getattr(existing_sm, attribute)
        else:
            raise ValueError(f"{key} is nor defined in the configuration nor in the existing scenario manager")
