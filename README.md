# PerfSim: A Performance Simulator for Cloud Native Microservice Chains
[![CodeQL](https://github.com/michelgokan/perfsim/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/michelgokan/perfsim/actions/workflows/github-code-scanning/codeql) [![Deploy Sphinx documentation to Pages](https://github.com/michelgokan/perfsim/actions/workflows/sphinx.yml/badge.svg)](https://github.com/michelgokan/perfsim/actions/workflows/sphinx.yml) [![pages-build-deployment](https://github.com/michelgokan/perfsim/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/michelgokan/perfsim/actions/workflows/pages/pages-build-deployment)
## Description

PerfSim is a discrete-event simulator designed to approximate and predict the performance of cloud-native
service chains in various user-defined scenarios. It leverages a systematic approach for analyzing network traces and
simulating the behavior of service chains to provide insights into system KPIs, such as the average response time of
requests.

> [!NOTE]
> The performance modeling part required to create the service chain models is not included in this suite. Users will
> need to prepare their models based on their own data or existing benchmarks.

---

> [!CAUTION]
> The current open source version of this package is a mere research prototype and is not intended for production use. 
> It is provided as-is, without any guarantees or warranties. Please do not consider this package as a fully functional 
> product at the moment. We are actively working on improving the package and adding new features, but we cannot provide
> any support for it at this time. There may or may not be a commercial version available soon, but we cannot guarantee.
> Use at your own risk. If you have any questions or concerns, please open an issue on the GitHub repository.

---

> [!CAUTION]
> This package contains several bugs and issues that we are actively working on fixing. Please be aware that the package
> may not work as expected in all cases. We are working on resolving these issues and will provide updates as soon as
> possible. If you encounter any problems, please open an issue on the GitHub repository, so we know.


## Features

- **Discrete-Event Simulation**: Offers precise simulation of cloud-native microservice behaviors over time.
- **User-Defined Scenarios**: Allows users to simulate custom scenarios, including different service chain
  configurations and resource allocation policies.
- **High Simulation Accuracy**: Achieves 81-99% simulation accuracy in predicting the average latency of incoming
  requests compared to real Kubernetes deployments.
- **Resource Efficiency**: Designed to run on modest hardware, such as a single laptop, facilitating large-scale
  simulations without the need for a real testbed.

## Limitations

While PerfSim provides valuable insights into the performance of cloud-native microservice chains, it has the following
limitations:

- **Modeling Exclusion**: PerfSim does not include a performance modeling component. Users must supply their own
  microservice performance models in JSON format or in the code.
- **Simulation Complexity**: For highly complex service chains with intricate dependencies and interactions, simulation
  results may vary from real-world deployments due to the abstraction level.
- **Resource Intensive Scenarios**: Extremely resource-intensive simulations may require hardware beyond a single laptop
  for optimal performance.
- **Networking Details**: Simplified networking simulation may not capture all nuances of real-world network behavior,
  particularly under specific or extreme conditions.

## Citation

If you use PerfSim in your scientific work, please consider citing us:

```
M. Gokan Khan, J. Taheri, A. Al-Dulaimy and A. Kassler, "PerfSim: A Performance Simulator for Cloud Native Microservice Chains," in IEEE Transactions on Cloud Computing, vol. 11, no. 2, pp. 1395-1413, 1 April-June 2023, doi: 10.1109/TCC.2021.3135757
```

Bibtex:

```
@ARTICLE{9652084,
  author={Gokan Khan, Michel and Taheri, Javid and Al-Dulaimy, Auday and Kassler, Andreas},
  journal={IEEE Transactions on Cloud Computing}, 
  title={PerfSim: A Performance Simulator for Cloud Native Microservice Chains}, 
  year={2023},
  volume={11},
  number={2},
  pages={1395-1413},
  keywords={Cloud computing;Computational modeling;Microservice architectures;Resource management;Emulation;Containers;Testing;Performance simulator;performance modeling;cloud native computing;service chains;simulation platform},
  doi={10.1109/TCC.2021.3135757}}
```

## Installation Instructions

1. Clone [PerfSim repository](https://github.com/michelgokan/perfsim) by running the following command:
  ```
  git clone git@github.com:michelgokan/perfsim.git
  ```

2. Navigate to the PerfSim directory:
   ```
   cd perfsim
   ```

3. Install dependencies (ensure you have Python 3.8 or later installed):
   ```
   pip install -r requirements.txt
   ```

## Usage

At the moment, there are 3 ways to run PerfSim scenarios:
1. **Run PerfSim via writing a Python script**: Users can write a Python script to define the simulation scenarios
      and run the simulation.
      There are examples under `tests` directory, where you can run as follows:

   ```
   pytest test_single_thread.py::Test1SFC1S1R1T1HBE::test_all_traffic_types_all_topologies
   ```

2. **Run PerfSim via web API(Flask)**: Users can run PerfSim via a web API. To run the web API, execute the following
   command:

    ```
    python server.py
    ```

   This will start the PerfSim server, and you can access via the following endpoints:

    - `/perfsim/`: To check if the server is running
    - `/perfsim/api/v1/config/setupAll`: To setup the simulation
    - `/perfsim/api/v1/scenario/run`: To run the simulation
    - `/perfsim/api/v1/scenario/saveAll`: To save the simulation results

3. **Run PerfSim via command line**: Users can run PerfSim via the command line. To run PerfSim via the command line,
   execute the following command:

    ```
    python perfsim.py --config <config_file_path> --scenario-id <scenario_id>
    ```

   e.g.,:
   ```
   python perfsim.py --config-path examples/example.json --scenario-id 1
   ```

You can then analyze the simulation results generated by PerfSim for performance insights.

## Rebuilding documentation

To rebuild the documentation, make sure to
first [install sphinx](https://www.sphinx-doc.org/en/master/usage/installation.html) and then run the following command:

```bash
cd docs
./rebuild_docs.sh
```

## Dependencies

PerfSim requires the following to run:

- Python 3.12 or later
- Additional Python libraries as listed in the `requirements.txt` file.

## Contributing

We welcome contributions to PerfSim! If you have suggestions for improvements or bug fixes, please fork the repository
and submit a pull request.

## License

PerfSim is released under the GPL V2 License. See the LICENSE file for more details.

## Contributors

- [Michel Gokan Khan](https://github.com/michelgokan) (main contributor)
- Maybe yourself? Send your first pull request to be listed here!

