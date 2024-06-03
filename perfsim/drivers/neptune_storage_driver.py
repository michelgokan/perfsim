from typing import TYPE_CHECKING, Dict

import neptune
from neptune import Run
from neptune.exceptions import InactiveRunException

from perfsim import ServiceChainManager, FileStorageDriver, Host

if TYPE_CHECKING:
    from perfsim import Simulation, Cluster


class NeptuneStorageDriver(FileStorageDriver):
    """
    Neptune storage driver is the class responsible for storing the results of the simulation in Neptune.
    """

    #: The Neptune handler.
    handler: Run

    def __init__(self, name: str, project_id: str, api_token: str):
        self.project_id = project_id
        self.api_token = api_token

        super().__init__(name)

    def init_neptune(self):
        """
        Initialize the Neptune handler.

        :return:
        """

        # Adjusted to updated import path
        self.handler = neptune.init(project=self.project_id, api_token=self.api_token)

    def save_simulation_scenario_results(self, simulation: 'Simulation'):
        """
        Save the results of the simulation scenario in Neptune.

        :param simulation:
        :return:
        """

        self.save_all(simulation)
        self.handler.stop()
        return "OK"

    def save_cluster_topology_graph(self, cluster: 'Cluster', save_dir="results/topologies"):
        """
        Save the topology graph of the cluster in Neptune.

        :param cluster:
        :param save_dir:
        :return:
        """

        content = super().save_cluster_topology_graph(cluster=cluster, save_dir=save_dir)
        self.handler[save_dir].upload(neptune.types.File.from_content(content, extension='html'))

    def save_service_chains_original_graph(self,
                                           service_chain_managers_dict: dict[str, ServiceChainManager],
                                           save_dir="results/service_chains/{middle}/original/{middle}"):
        """
        Save the original service chains graph in Neptune.

        :param service_chain_managers_dict:
        :param save_dir:
        :return:
        """

        contents = super().save_service_chains_original_graph(service_chain_managers_dict=service_chain_managers_dict,
                                                              save_dir=save_dir)
        for save_folder, content in contents.items():
            self.handler[save_folder].upload(neptune.types.File.from_content(content, extension='html'))

        return contents

    def save_service_chains_alternative_graph(self,
                                              service_chain_managers_dict: dict[str, ServiceChainManager],
                                              save_dir="results/service_chains/{middle}/alternative"):
        """
        Save the alternative service chains graph in Neptune.

        :param service_chain_managers_dict:
        :param save_dir:
        :return:
        """

        contents = super().save_service_chains_alternative_graph(
            service_chain_managers_dict=service_chain_managers_dict,
            save_dir=save_dir)

        for save_folder, content in contents.items():
            self.handler[save_folder].upload(neptune.types.File.from_content(content, extension='html'))

        return contents

    def save_service_chain_result_graph(self, result, save_dir="results/{result_key}"):
        """
        Save the service chain result graph in Neptune.

        :param result:
        :param save_dir:
        :return:
        """

        contents = super().save_service_chain_result_graph(result=result, save_dir=save_dir)
        save_dir = save_dir.format(middle="summary", result_key="results")
        file_path = save_dir + ".json"

        try:
            self.handler[save_dir].upload(file_path)
        except (InactiveRunException, AttributeError) as e:
            self.init_neptune()
            self.handler[save_dir].upload(file_path)

        for save_path, content in contents.items():
            if save_path.endswith("_json"):
                file_path = save_path[:-len("_json")] + ".json"
                self.handler[save_path].track_files(file_path)
            elif not save_path.endswith("_raw"):
                self.handler[save_path].upload(neptune.types.File.as_html(content))
            else:
                self.handler[save_path].log(content)

        return contents

    def save_timeline_graph(self, result, save_dir="results/timeline"):
        """
        Save the timeline graph in Neptune.

        :param result:
        :param save_dir:
        :return:
        """

        fig = super().save_timeline_graph(result=result, save_dir=save_dir)
        self.handler[save_dir].upload(neptune.types.File.as_html(fig))
        return fig

    def save_hosts_cores_heatmap(self, hosts_dict: Dict[str, Host], save_dir: str = "results/cpu/heatmap/{result_key}"):
        """
        Save the hosts cores heatmap in Neptune.

        :param hosts_dict:
        :param save_dir:
        :return:
        """

        figs = super().save_hosts_cores_heatmap(hosts_dict=hosts_dict, save_dir=save_dir)

        for host_name, fig in figs.items():
            save_path = save_dir.format(result_key=host_name)
            self.handler[save_path + "/" + host_name + "-threads-lb-cpu_requests_share.html"].upload(
                neptune.types.File.as_html(fig[0]))
            self.handler[save_path + "/" + host_name + "-threads-lb-threads.html"].upload(
                neptune.types.File.as_html(fig[1]))

        return figs
