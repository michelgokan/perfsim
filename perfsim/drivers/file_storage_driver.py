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


from typing import TYPE_CHECKING, Dict

import plotly.express as px

from perfsim import ResultsStorageDriver, SimulationScenarioResultDict, ServiceChainManager, Utils, Plotter, Host

if TYPE_CHECKING:
    from perfsim import Simulation, Cluster


class FileStorageDriver(ResultsStorageDriver):
    """
    File storage driver is the class responsible for storing the results of the simulation in a file system.
    """

    #: The base directory where the results will be stored.
    base_dir: str

    def __init__(self, name: str, base_dir: str = "results/"):
        super().__init__(name)
        self.base_dir = base_dir

    def save_all(self, simulation: 'Simulation'):
        """
        Save all the results of the simulation in the file system.

        :param simulation:
        :return:
        """
        result: SimulationScenarioResultDict = simulation.load_generator.get_latencies_grouped_by_sfc()
        s = self.base_dir + "/" + simulation.name + '/{middle}/{result_key}'
        self.results_with_graphs = {
            'result': result,
            'service_chain': self.save_service_chain_result_graph(result=result,
                                                                  save_dir=s.format(middle="{middle}",
                                                                                    result_key="{result_key}")),
            'topology': self.save_cluster_topology_graph(cluster=simulation.cluster,
                                                         save_dir=s.format(middle="topology", result_key="")),
            'sfcs_original': self.save_service_chains_original_graph(
                service_chain_managers_dict=simulation.cluster.scm_dict,
                save_dir=s.format(middle="{middle}", result_key="service_chains/original")),
            'sfcs_alternative': self.save_service_chains_alternative_graph(
                service_chain_managers_dict=simulation.cluster.scm_dict,
                save_dir=s.format(middle="{middle}", result_key="service_chains/alternative")),
            'timeline': self.save_timeline_graph(result=result, save_dir=self.base_dir + '/timeline'),
            'cores_heatmap': self.save_hosts_cores_heatmap(hosts_dict=simulation.cluster.cluster_scheduler.hosts_dict,
                                                           save_dir=s.format(middle="hosts/{result_key}/cpu/heatmap",
                                                                             result_key=""))}
        return self.results_with_graphs

    def save_simulation_scenario_results(self, simulation: 'Simulation'):
        """
        Save the results of the simulation scenario in the file system.

        :param simulation:
        :return:
        """

        return self.save_all(simulation)

    def save_cluster_topology_graph(self, cluster: 'Cluster', save_dir="results/topologies"):
        """
        Save the topology graph of the cluster in the file system.

        :param cluster:
        :param save_dir:
        :return:
        """

        return cluster.topology.draw(show_microservices=True, save_dir=save_dir)

    def save_service_chains_original_graph(self,
                                           service_chain_managers_dict: dict[str, ServiceChainManager],
                                           save_dir="results/service_chains/{middle}/original") -> dict[str, str]:
        """
        Save the original service chains graph of the service chain managers in the file system.

        :param service_chain_managers_dict:
        :param save_dir:
        :return:
        """

        contents = {}

        for scm in service_chain_managers_dict.values():
            s = save_dir.format(middle=scm.name)
            content = scm.draw_service_chain(save_dir=s)
            contents[s] = content

        return contents

    def save_service_chains_alternative_graph(self,
                                              service_chain_managers_dict: dict[str, ServiceChainManager],
                                              save_dir="results/service_chains/{middle}/alternative") -> dict[str, str]:
        """
        Save the alternative service chains graph of the service chain managers in the file system.

        :param service_chain_managers_dict:
        :param save_dir:
        :return:
        """

        contents = {}

        for scm in service_chain_managers_dict.values():
            s = save_dir.format(middle=scm.name)
            content = scm.draw_alternative_graph(save_dir=s)
            contents[s] = content

        return contents

    def save_service_chain_result_graph(self, result, save_dir="results/{result_key}"):
        """
        Save the results of the service chains in the file system.

        :param result:
        :param save_dir:
        :return:
        """

        contents = {}
        Utils.save_results_json(result=result, save_dir=save_dir.format(middle="summary", result_key="results"))

        for sfc in result["service_chains"]:
            for result_key, result_value in result["service_chains"][sfc].items():
                if result_key == "simulation_name":
                    continue
                s_sfc = save_dir.format(middle=sfc, result_key=result_key)
                # s = s_summary.format(result_key=result_key)
                if type(result_value) == dict:
                    if result_key != "traffic_types":
                        save_path = s_sfc + ".html"
                        Utils.mkdir_p(save_path)
                        r = list(result_value.values())
                        fig = px.line(y=r, color=px.Constant("latencies"), labels=dict(x="Request ID", y=result_key))
                        fig.add_bar(y=r, name="latencies")
                        fig.write_html(save_path)
                        contents[s_sfc] = fig
                    contents[s_sfc + "_json"] = result_value
                    Utils.save_results_json(result=result_value, save_dir=s_sfc)
                else:
                    contents[s_sfc + "_raw"] = result_value

        return contents

    def save_timeline_graph(self, result, save_dir: str = "results/{result_key}"):
        """
        Save the timeline graph of the results in the file system.

        :param result:
        :param save_dir:
        :return:
        """

        fig = Plotter.draw_timeline_graph(results=result)
        fig.write_html(save_dir + ".html")
        return fig

    def save_hosts_cores_heatmap(self, hosts_dict: Dict[str, Host], save_dir: str = "results/cpu/heatmap/{result_key}"):
        """
        Save the hosts cores heatmap graph in the file system.

        :param hosts_dict:
        :param save_dir:
        :return:
        """

        figs = {}

        for host_name, host in hosts_dict.items():
            figs[host_name] = host.cpu.plot(save_dir=save_dir.format(result_key=""), show=False)

        return figs
