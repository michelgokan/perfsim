import json
import math
import os
import traceback
from math import floor
from typing import List, Dict, Union

import numpy as np
import pytest

from perfsim import MicroservicePrototype, MicroserviceEndpointFunctionPrototype, HostPrototype, RouterPrototype, \
    TopologyLinkPrototype, TrafficPrototype, LeastFit, TopologyPrototype, ServiceChain, PlacementAlgorithm, \
    ResourceAllocationScenario, FileStorageDriver, Microservice, SimulationScenarioManager, TrafficScenario, \
    ScalingScenario, DebugDict, ServiceChainLink, SimulationScenario, ResourceNotAvailableError
from perfsim import PerfSimServer
from tests.helpers import putils

pytest.DEBUG_LEVEL = 0
pytest.gen_mode = True  #: When pytest.gen_mode is set to True, the expected values are generated and saved to the file


def get_simulation_scenario(traffic_scenario, scaling_scenarios, topo_name) -> SimulationScenario:
    return {
        "name": "sim1",
        "traffic_scenario": traffic_scenario,
        "scaling_scenarios": scaling_scenarios,
        "affinity_scenarios": [],
        "placement_algorithm": "least_fit_placement_simple",
        "topology": topo_name,
        "network_timeout": -1,
        "debug": DebugDict(debug=True,
                           debug_level=pytest.DEBUG_LEVEL,
                           debug_file_location=None,
                           log_cpu_events=True,
                           log_timeline=True)
    }


def create_sim_manager(traffic_type: TrafficPrototype,
                       topology_prototype: TopologyPrototype,
                       sfc: ServiceChain,
                       placement_algorithm: PlacementAlgorithm,
                       ras: ResourceAllocationScenario,
                       driver: FileStorageDriver,
                       scaling_scenarios: List[ScalingScenario]) -> SimulationScenarioManager:
    ts = TrafficScenario(name="single_request", service_chains={sfc.name: {"traffic_type": traffic_type.name}})

    sim_scenario = pytest.get_simulation_scenario(traffic_scenario=ts,
                                                  scaling_scenarios=scaling_scenarios,
                                                  topo_name=topology_prototype.name)

    return SimulationScenarioManager(simulation_scenarios=[sim_scenario],
                                     service_chains=[sfc],
                                     topology_prototypes=[topology_prototype],
                                     placement_algorithms=[placement_algorithm],
                                     res_alloc_scenarios=[ras],
                                     affinity_prototypes=[],
                                     traffic_prototypes=[traffic_type],
                                     results_storage_driver=driver)


def exec_scenario(traffic_prototype: TrafficPrototype,
                  tau: TopologyPrototype,
                  sfc: ServiceChain,
                  microservices: List[Microservice],
                  replica_count: int,
                  resource_allocation_scenario: ResourceAllocationScenario,
                  number_of_threads: int) -> Union[None, SimulationScenarioManager]:
    try:
        ss = []
        ms_dict = {
            ms.name: {
                "replica_count": replica_count,
                "resource_allocation_scenario": resource_allocation_scenario.name
            } for ms in microservices}
        ss.append(ScalingScenario(microservice=ms_dict))
        m: Union[None, SimulationScenarioManager] = pytest.create_sim_manager(
            traffic_type=traffic_prototype,
            topology_prototype=tau,
            sfc=sfc,
            placement_algorithm=pytest.least_fit_placement_algorithm,
            ras=resource_allocation_scenario,
            driver=pytest.driver,
            scaling_scenarios=ss)
        thread_count_in_english = str(number_of_threads) + ("_threads" if number_of_threads > 1 else "_thread")
        m.results_storage_driver.base_dir = \
            f"results/{thread_count_in_english}/{traffic_prototype.name}/{tau.name}/{resource_allocation_scenario.name}"
        m.simulations_dict["sim1"].load_generator.execute_traffic()
        m.save_all()
    except ResourceNotAvailableError:
        m = None
    except Exception as e:
        print("\nAn exception occurred:", type(e))
        print("\nMore info:", repr(e))
        traceback.print_exc()

        raise e

    return m


def get_traffic_topology_expected_combination(file_name: str,
                                              include_guaranteed_only: bool = False,
                                              include_burstable_only: bool = False,
                                              include_mixed_only: bool = False,
                                              gen_mode: bool = False,
                                              topology_protos: Union[None, Dict[str, TopologyPrototype]] = None):
    """
    # When pytest.gen_mode is set to True, the expected values are generated and saved to the file
    """
    traf_topo_combs = []
    test_names = []
    topology_protos = pytest.t if topology_protos is None else topology_protos

    if include_guaranteed_only:
        resources = pytest.ras_guaranteed.items()
    elif include_burstable_only:
        resources = pytest.ras_burstable.items()
    elif include_mixed_only:
        resources = pytest.ras_burstable.items()
    else:
        resources = {0: "best_effort"}.items()

    for millicores, ras in resources:
        filepath = "expected_results/" + file_name + "_" + str(millicores) + ".json"
        if gen_mode:
            if os.path.exists(filepath):
                os.remove(filepath)
            expected_avg_lats_json = None
        else:
            expected_avg_lats_json = json.load(open(filepath))

        for _traffic_name in pytest.traffic_prototypes:
            for _topo_name in topology_protos:
                if expected_avg_lats_json is not None:
                    expected_avg_lats_traffic = expected_avg_lats_json["traffic_types"][_traffic_name]
                    expected_avg_lats_topology_type = expected_avg_lats_traffic["topology_types"][_topo_name]
                else:
                    expected_avg_lats_topology_type = None
                traf_topo_combs.append((_traffic_name, _topo_name, expected_avg_lats_topology_type, ras, filepath))
                test_names.append(f"{_traffic_name}_{_topo_name}_{ras}")

    return traf_topo_combs, test_names


def assertions(m, traff_proto_name, topo_name, expected_avg_lats_obj, ras, sfc, gen_mode, filepath, err_margin=0.001):
    if gen_mode:
        pytest.generate_actual(m, traff_proto_name, topo_name, ras, sfc, filepath, err_margin)
    else:
        expected_avg_lats = expected_avg_lats_obj['service_chains'][sfc.name]

        if m is None:
            assert expected_avg_lats['expected_min'] == "Resource Error"
        else:
            actual_avg_lats_results = m.results_storage_driver.results_with_graphs['result']['service_chains']
            actual_avg_lats = actual_avg_lats_results[sfc.name]['avg_latency']
            pytest.print_additional_logs(traff_proto_name, topo_name, ras, actual_avg_lats, expected_avg_lats)
            expected_min = expected_avg_lats['expected_min']
            expected_max = expected_avg_lats['expected_max']
            assert _assert_latency(expected_min, actual_avg_lats, expected_max)


def _assert_latency(expected_min, actual_avg_lats, expected_max):
    if not expected_min <= actual_avg_lats <= expected_max:
        raise AssertionError(f"Expected: {expected_min} <= Actual: {actual_avg_lats} <= {expected_max}")
    else:
        return True


def generate_actual(m, traff_proto_name, topo_name, ras, sfc, filepath, err_margin=0.001):
    if m is None:
        actual_avg_lats_min = actual_avg_lats_max = actual_avg_lats = "Resource Error"
    else:
        actual_avg_lats_results = m.results_storage_driver.results_with_graphs['result']['service_chains']
        actual_avg_lats = actual_avg_lats_results[sfc.name]['avg_latency']
        acceptable_error = math.ceil(err_margin * actual_avg_lats)
        actual_avg_lats_min = actual_avg_lats - acceptable_error
        actual_avg_lats_max = actual_avg_lats + acceptable_error
    try:
        json_obj = json.load(open(filepath))
    except FileNotFoundError:
        json_obj = {"traffic_types": {}}
    if traff_proto_name not in json_obj["traffic_types"]:
        json_obj["traffic_types"][traff_proto_name] = {"topology_types": {}}
    if topo_name not in json_obj["traffic_types"][traff_proto_name]["topology_types"]:
        json_obj["traffic_types"][traff_proto_name]["topology_types"][topo_name] = {"service_chains": {}}

    json_obj["traffic_types"][traff_proto_name]["topology_types"][topo_name]["service_chains"][sfc.name] = \
        {"expected_min": actual_avg_lats_min, "expected_max": actual_avg_lats_max, "expected_actual": actual_avg_lats}
    with open(filepath, 'w') as f:
        json.dump(json_obj, f, indent=2)


def print_additional_logs(traff_proto_name, topo_name, ras, actual_avg_lats, expected_avg_lats):
    # Plotter.draw_figures(load_generator=m.simulations_dict['sim1'].load_generator, scenario_name='sim1')
    print()
    print("Arguments: ", traff_proto_name + " " + topo_name + " " + str(ras))
    print("actual_avg_lats: " + str(actual_avg_lats))
    print("expected_avg_lats[min]: " + str(expected_avg_lats['expected_min']))
    print("expected_avg_lats[max]: " + str(expected_avg_lats['expected_max']))


pytest.assertions = assertions
pytest.generate_actual = generate_actual
pytest.print_additional_logs = print_additional_logs
pytest.get_simulation_scenario = get_simulation_scenario
pytest.cpu_intensive_ms_proto_single_thread = MicroservicePrototype(name="simple_cpu_intensive_service")
pytest.cpu_intensive_ms_proto_double_thread = MicroservicePrototype(name="simple_cpu_intensive_service")
# super(BaseTest, self).__init__(*args, **kwargs)
pytest.single_threaded_endpoint_proto = MicroserviceEndpointFunctionPrototype(
    name="single_threaded_endpoint",
    id=0,
    threads_instructions=[1209325186],
    threads_avg_cpi=[0.76008072],
    threads_avg_cpu_usages=[1],
    threads_avg_mem_accesses=[414016086],
    threads_single_core_isolated_cache_misses=[75266],
    threads_single_core_isolated_cache_refs=[799434],
    threads_avg_cache_miss_penalty=[5.71],
    threads_avg_blkio_rw=[0],
    request_timeout=-1,
    microservice_prototype=pytest.cpu_intensive_ms_proto_single_thread)
pytest.double_threaded_endpoint_proto = MicroserviceEndpointFunctionPrototype(
    name="double_threaded_endpoint",
    id=0,
    threads_instructions=[1209325186, 1209325186],
    threads_avg_cpi=[0.76008072, 0.76008072],
    threads_avg_cpu_usages=[1, 1],
    threads_avg_mem_accesses=[414016086, 414016086],
    threads_single_core_isolated_cache_misses=[75266, 75266],
    threads_single_core_isolated_cache_refs=[799434, 799434],
    threads_avg_cache_miss_penalty=[5.71, 5.71],
    threads_avg_blkio_rw=[0, 0],
    request_timeout=-1,
    microservice_prototype=pytest.cpu_intensive_ms_proto_double_thread)
pytest.cpu_intensive_ms_proto_single_thread.add_endpoint_function_prototype(pytest.single_threaded_endpoint_proto)
pytest.cpu_intensive_ms_proto_double_thread.add_endpoint_function_prototype(pytest.double_threaded_endpoint_proto)

hosts_combination = {"cores_count": [1, 2, 4, 8]}
pytest.host_prototypes = {}
for core_count in hosts_combination["cores_count"]:
    core_or_cores = "cores" if core_count > 1 else "core"
    name = f"{core_count}{core_or_cores}_host_scenario"
    pytest.host_prototypes[name] = HostPrototype(name=name,
                                                 cpu_core_count=core_count,
                                                 cpu_clock_rate=1596090000,
                                                 memory_capacity=16,
                                                 ram_speed=2675787694,
                                                 storage_capacity=1000,
                                                 storage_speed=10695000,
                                                 network_bandwidth=117300000)

pytest.simple_10g_router_prototype = RouterPrototype(name="simple_10g_router",
                                                     latency=730000,
                                                     egress_ingress_bw=1250000000,
                                                     ports_count=101)
pytest.simple_link_prototype = TopologyLinkPrototype(name="simple_link", latency=420000)

# batchps = Batch Request per Second
traffic_type_combination = {"arrival_rates": np.arange(1, 4), "duration": [1, 60], "parallel_user": [1, 2]}
pytest.traffic_prototypes = {}
for arrival_rate in traffic_type_combination["arrival_rates"]:
    for duration in traffic_type_combination["duration"]:
        for parallel_user in traffic_type_combination["parallel_user"]:
            name = f"{arrival_rate}batchps_{duration}sec_{parallel_user}paralleluser"
            pytest.traffic_prototypes[name] = TrafficPrototype(name=name,
                                                               arrival_interval_ns=floor(1000000000 / arrival_rate),
                                                               duration=duration,
                                                               parallel_user=parallel_user)

least_fit_options = dict(w_cpu=100, w_mem=100, w_ingress=100, w_egress=100, w_blkio=0)
pytest.least_fit_placement_algorithm = LeastFit(name="least_fit_placement_simple", options=least_fit_options)
pytest.create_sim_manager = create_sim_manager
pytest.exec_scenario = exec_scenario

pytest.ms1_single_thread = Microservice.from_prototype(name="ms1_single_thread",
                                                       prototype=pytest.cpu_intensive_ms_proto_single_thread,
                                                       replica_count=1)
pytest.ms1_double_thread = Microservice.from_prototype(name="ms1_double_thread",
                                                       prototype=pytest.cpu_intensive_ms_proto_double_thread,
                                                       replica_count=1)
pytest.ms2_single_thread = Microservice.from_prototype(name="ms2_single_thread",
                                                       prototype=pytest.cpu_intensive_ms_proto_single_thread,
                                                       replica_count=1)
pytest.ms2_double_thread = Microservice.from_prototype(name="ms2_double_thread",
                                                       prototype=pytest.cpu_intensive_ms_proto_double_thread,
                                                       replica_count=1)
pytest.ms1_f1_single_thread = pytest.ms1_single_thread.endpoint_functions["single_threaded_endpoint"]
pytest.ms1_f1_double_thread = pytest.ms1_double_thread.endpoint_functions["double_threaded_endpoint"]
pytest.ms2_f1_single_thread = pytest.ms2_single_thread.endpoint_functions["single_threaded_endpoint"]
pytest.ms2_f1_double_thread = pytest.ms2_double_thread.endpoint_functions["double_threaded_endpoint"]
pytest.ms1_f1_ms2_f1_single_thread_link = ServiceChainLink(name="ms1_f1_ms2_f1_single_thread_link",
                                                           request_size=100000,
                                                           source=pytest.ms1_f1_single_thread,
                                                           dest=pytest.ms2_f1_single_thread)
pytest.ms1_f1_ms2_f1_double_thread_link = ServiceChainLink(name="ms1_f1_ms2_f1_single_thread_link",
                                                           request_size=100000,
                                                           source=pytest.ms1_f1_double_thread,
                                                           dest=pytest.ms2_f1_double_thread)

pytest.driver = FileStorageDriver(name="file_storage_driver1")
# pytest.driver = NeptuneStorageDriver(name="neptune_storage_driver1",
#                                      project_id="PerfSim-Integration-Test",
#                                      api_token="eyJhcGlfYWRkcmVzcyI6Imh0dHBzOi8vYXBwLm5lcHR1bmUuYWkiLCJhcGlfdXJsIjoiaHR"
#                                                "0cHM6Ly9hcHAubmVwdHVuZS5haSIsImFwaV9rZXkiOiIyODJhZjFhZS0wZDA2LTRiYWMtOT"
#                                                "BkYi1jZGZiNWE4MGQzMWEifQ==")
pytest.ras_best_effort = ResourceAllocationScenario(name="test_best_effort",
                                                    cpu_requests=-1,
                                                    cpu_limits=-1,
                                                    memory_requests=0,
                                                    ingress_bw="",
                                                    egress_bw="",
                                                    ingress_latency=0,
                                                    egress_latency=0,
                                                    blkio_capacity=0)
pytest.ras_guaranteed = {100: ResourceAllocationScenario(name="test_guaranteed_100",
                                                         cpu_requests=100,
                                                         cpu_limits=100,
                                                         memory_requests=0,
                                                         ingress_bw="",
                                                         egress_bw="",
                                                         ingress_latency=0,
                                                         egress_latency=0,
                                                         blkio_capacity=0),
                         500: ResourceAllocationScenario(name="test_guaranteed_500",
                                                         cpu_requests=500,
                                                         cpu_limits=500,
                                                         memory_requests=0,
                                                         ingress_bw="",
                                                         egress_bw="",
                                                         ingress_latency=0,
                                                         egress_latency=0,
                                                         blkio_capacity=0),
                         1000: ResourceAllocationScenario(name="test_guaranteed_1000",
                                                          cpu_requests=1000,
                                                          cpu_limits=1000,
                                                          memory_requests=0,
                                                          ingress_bw="",
                                                          egress_bw="",
                                                          ingress_latency=0,
                                                          egress_latency=0,
                                                          blkio_capacity=0),
                         2000: ResourceAllocationScenario(name="test_guaranteed_1000",
                                                          cpu_requests=2000,
                                                          cpu_limits=2000,
                                                          memory_requests=0,
                                                          ingress_bw="",
                                                          egress_bw="",
                                                          ingress_latency=0,
                                                          egress_latency=0,
                                                          blkio_capacity=0)}
pytest.ras_burstable = {100: ResourceAllocationScenario(name="test_burstable_100",
                                                        cpu_requests=100,
                                                        cpu_limits=-1,
                                                        memory_requests=0,
                                                        ingress_bw="",
                                                        egress_bw="",
                                                        ingress_latency=0,
                                                        egress_latency=0,
                                                        blkio_capacity=0),
                        500: ResourceAllocationScenario(name="test_burstable_500",
                                                        cpu_requests=500,
                                                        cpu_limits=600,
                                                        memory_requests=0,
                                                        ingress_bw="",
                                                        egress_bw="",
                                                        ingress_latency=0,
                                                        egress_latency=0,
                                                        blkio_capacity=0),
                        1000: ResourceAllocationScenario(name="test_burstable_1000",
                                                         cpu_requests=1000,
                                                         cpu_limits=-1,
                                                         memory_requests=0,
                                                         ingress_bw="",
                                                         egress_bw="",
                                                         ingress_latency=0,
                                                         egress_latency=0,
                                                         blkio_capacity=0),
                        2000: ResourceAllocationScenario(name="test_burstable_1000",
                                                         cpu_requests=2000,
                                                         cpu_limits=-1,
                                                         memory_requests=0,
                                                         ingress_bw="",
                                                         egress_bw="",
                                                         ingress_latency=0,
                                                         egress_latency=0,
                                                         blkio_capacity=0)}

pytest.sfc_one_service_one_thread = ServiceChain(name="sfc1_1s_1thread", nodes=[pytest.ms1_f1_single_thread], edges=[])
pytest.sfc_one_service_two_thread = ServiceChain(name="sfc1_1s_2thread", nodes=[pytest.ms1_f1_double_thread], edges=[])
pytest.sfc_two_services_one_thread = ServiceChain(name="sfc1_2s_1thread",
                                                  nodes=[pytest.ms1_f1_single_thread, pytest.ms2_f1_single_thread],
                                                  edges=[pytest.ms1_f1_ms2_f1_single_thread_link])
pytest.sfc_two_services_two_thread = ServiceChain(name="sfc1_2s_2thread",
                                                  nodes=[pytest.ms1_f1_double_thread, pytest.ms2_f1_double_thread],
                                                  edges=[pytest.ms1_f1_ms2_f1_double_thread_link])

pytest.t, pytest.h, pytest.r, pytest.l = \
    putils.create_host_topology_prototypes(r_proto=pytest.simple_10g_router_prototype,
                                           l_proto=pytest.simple_link_prototype,
                                           max_host_count=1)

pytest.t1, pytest.h1, pytest.r1, pytest.l1 = \
    putils.create_host_topology_prototypes(r_proto=pytest.simple_10g_router_prototype,
                                           l_proto=pytest.simple_link_prototype,
                                           max_host_count=1)

pytest.t2, pytest.h2, pytest.r2, pytest.l2 = \
    putils.create_host_topology_prototypes(r_proto=pytest.simple_10g_router_prototype,
                                           l_proto=pytest.simple_link_prototype,
                                           max_host_count=2)
pytest.get_traffic_topology_expected_combination = get_traffic_topology_expected_combination

pytest.test_attributes = 'traff_proto_name,topo_name,expected_avg_lats_obj,ras,filepath'


# pytest.ms = Microservice.from_prototype(name="ms1", prototype=pytest.cpu_intensive_ms_proto, replica_count=1)


@pytest.fixture(scope='class')
def server_app():
    """Create and configure a new app instance for each test."""
    server = PerfSimServer()
    yield server.server


@pytest.fixture(scope='class')
def client(server_app):
    """A test client for the app."""
    return server_app.test_client()
