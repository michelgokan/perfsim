import json
import logging
from pathlib import Path
from time import perf_counter
from typing import Callable, Union

from dash import Dash, html
from flask import Flask, request, Response, make_response, jsonify
from single_source import get_version

from perfsim import SimulationScenarioManager, ResponseException


class PerfSimServer:
    """
    The PerfSimServer class is a wrapper for the Flask server that handles the simulation requests.
    It is responsible for the following:
        - Initializing the Flask server
        - Handling the simulation requests
        - Handling the errors via populating appropriate responses
    """

    #: The Flask server
    server: Flask

    #: The Dash app
    app: Dash

    #: The host address
    _host: str

    #: The port number of the server
    _port: int

    #: Enable/disable the performance logging
    perf_logs: bool

    #: The SimulationScenarioManager object, created from the scenario/config
    sm: Union[SimulationScenarioManager, None]

    def __init__(self,
                 host: str = '0.0.0.0',
                 port: int = 8081,
                 perf_logs: bool = True,
                 log_filename: str = None,
                 log_format: str = None,
                 log_level: int = logging.INFO,
                 debug: bool = False):
        """
        Initialize the server.

        :param host: The host address for the server. Default is '0.0.0.0'
        :param port: The port for the server. Default is 8081.
        :param perf_logs: Enable/disable the logs related to the execution time of math functions. Default is True.
        :param log_filename: The filename for the log file. If None, the log will be written to the console.
        :param log_format: The format for the log file. If None, the default format will be used.
        :param log_level: The log level based on the logging module. If None, the logging.INFO will be used.
        :param debug: Enable/disable the debug mode. Default is False.
        """

        self._set_connection_params(host, port)
        self.perf_logs = perf_logs
        self.app = Dash(name=__name__, url_base_pathname='/dash/')
        self.server = self.app.server
        self.app.layout = html.Div(id='dash-container')
        self.app.debug = debug
        logging.basicConfig(level=log_level, filename=log_filename, format=log_format)
        self.configure_routes()
        self.sm = None
        # self.sm = SimulationScenarioManager()

    def run(self) -> None:
        """
        Run the server.

        :return: None
        """

        self.app.run_server(host=self.host, port=self.port)

    def _set_connection_params(self, host_address: str, port: int) -> None:
        """
        Set the host address and port for the server.

        :param host_address: The host address for the server.
        :param port: The port for the server.
        :return: None
        """

        self._host = host_address
        self._port = port

    def create_scenario_manager(self):
        """
        Create a scenario manager from the configuration.

        :return:
        """

        config = json.loads(request.form.get("config"))
        self.sm = SimulationScenarioManager.from_config(conf=config, existing_scenario_manager=self.sm)
        return "ok"

    def _validate_sim(self):
        """
        Validate the simulation scenario manager.

        :return:
        """

        if self.sm is None:
            return self.make_error_response(error_code=500,
                                            error_message="No scenario created, please setup a scenario "
                                                          "first via /perfsim/api/v1/scenario/setupAll.")

    def run_scenario(self):
        """
        Run the scenario.

        :return:
        """

        self._validate_sim()

        try:
            load_generator = self.sm.simulations_dict[request.args.get("id")].load_generator
        except KeyError:
            return self.make_error_response(error_code=500,
                                            error_message="Scenario " + str(request.args.get("id")) + " not found.")
        load_generator.execute_traffic()
        result = self.sm.get_all_latencies()

        return json.dumps(result)

    def save_all(self):
        """
        Save all the results.

        :return:
        """

        self._validate_sim()
        self.sm.save_all()
        return "ok"

    def configure_routes(self) -> None:
        """
        Configure the routes for the server.

        :return: None
        """

        @self.server.route('/perfsim/api/v1/config/setupAll', methods=['POST'])
        def setup_scenario():
            return self.make_function_response(func=self.create_scenario_manager)

        @self.server.route('/perfsim/api/v1/scenario/run', methods=['GET'])
        def run_scenario():
            return self.make_function_response(func=self.run_scenario)

        @self.server.route('/perfsim/api/v1/saveAll', methods=['GET'])
        def save_all():
            return self.make_function_response(func=self.save_all)

        @self.server.route('/perfsim/', methods=['GET'])
        def index() -> str:
            """
            Setup the route for the index page which displays the current version of the PerfSim.
            :return: The version of the PerfSim (e.g., perfsim v1.0.0)
            """

            current_version = get_version(__name__, Path(__file__).parent.parent)
            return "PerfSim v" + current_version

    @staticmethod
    def make_error_response(error_code: int, error_message: str) -> Response:
        """
        Make an error response.

        :param error_code: The error code.
        :param error_message: The error message.
        :return: The error response.
        """

        raise ResponseException(str(error_code) + ": " + error_message)

    def make_function_response(self, func: Callable, *args) -> Response:
        """
        Make a response for a function call.

        :param func: The function to call.
        :param args: The arguments to pass to the function.
        :return: The response of type Response.
        """

        try:
            if self.perf_logs:
                start_time = perf_counter()
                result = func(*args)
                end_time = perf_counter()
                duration = end_time - start_time
                self.app.logger.info("Function call of {} took {} seconds".format(func.__name__, duration))
            else:
                result = func(*args)

            return make_response(jsonify({'result': result}), 200)
        except ValueError as e:
            return make_response(jsonify({"error": str(e)}), 400)
        except ResponseException as e:
            return make_response(jsonify({"error": str(e)}), 400)

    @property
    def host(self):
        """
        Get the host address.

        :return:
        """

        return self._host

    @property
    def port(self):
        """
        Get the port number.

        :return:
        """

        return self._port

    @host.setter
    def host(self, host_address: str):
        """
        Set the host address.

        :param host_address:
        :return:
        """

        raise NotImplementedError("The host address cannot be changed.")

    @port.setter
    def port(self, port: int):
        """
        Set the port number.

        :param port:
        :return:
        """

        raise NotImplementedError("The port cannot be changed.")
