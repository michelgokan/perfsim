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

import pytest


@pytest.mark.usefixtures("client", "server_app")
class Test1SFC1S1R1T1HGE:  # GE = guaranteed
    def test_all_traffic_types_all_topologies(self):
        for traffic_name in pytest.traffic_prototypes:
            for topo_name in pytest.t:
                # if traffic_name == '3batchps_60sec_2paralleluser' \
                # and topo_name == 'tau_1host_8cores_host_scenario':
                pytest.exec_scenario(traffic_prototype=pytest.traffic_prototypes[traffic_name],
                                     tau=pytest.t[topo_name],
                                     sfc=pytest.sfc_one_service_one_thread,
                                     microservices=[pytest.ms1_single_thread],
                                     replica_count=1,
                                     resource_allocation_scenario=pytest.ras_best_effort,
                                     number_of_threads=1)
