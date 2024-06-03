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

from perfsim import SimulationScenarioManager

test_name = "single_thread_expected_results"
traffic_topology_combs, names = pytest.get_traffic_topology_expected_combination(file_name=test_name,
                                                                                 gen_mode=pytest.gen_mode)
sfc = pytest.sfc_one_service_one_thread


@pytest.mark.usefixtures("client", "server_app")
class Test1SFC1S1R1T1HBE:
    @pytest.mark.parametrize(pytest.test_attributes, traffic_topology_combs, ids=names)
    def test_all_traffic_types_all_topologies(self, traff_proto_name, topo_name, expected_avg_lats_obj, ras, filepath):
        # if traff_proto_name == "2batchps_1sec_1paralleluser" and topo_name == "tau_1host_4cores_host_scenario":
        m: SimulationScenarioManager = pytest.exec_scenario(
            traffic_prototype=pytest.traffic_prototypes[traff_proto_name],
            tau=pytest.t[topo_name],
            sfc=sfc,
            microservices=[pytest.ms1_single_thread],
            replica_count=1,
            resource_allocation_scenario=pytest.ras_best_effort,
            number_of_threads=1)
        pytest.assertions(m, traff_proto_name, topo_name, expected_avg_lats_obj, ras, sfc, pytest.gen_mode, filepath)
