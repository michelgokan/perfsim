import json
import sys

from perfsim import SimulationScenarioManager, ResponseException


# A function to print usage
def print_usage():
    print("Usage: python3 perfsim.py --config <path_to_config_file> --scenario-id <scenario_id>")
    sys.exit(1)


# Check if 2 parameters --config and --scenario-id is given from command line (the order shouldn't matter)
if "--config" not in sys.argv or "--scenario-id" not in sys.argv:
    print_usage()
# Check if config file exists
config_path = sys.argv[sys.argv.index("--config") + 1]
try:
    with open(config_path, 'r') as file:
        config = json.load(file)
except FileNotFoundError:
    print(f"Config file not found: {config_path}")
    sys.exit(1)

sm = SimulationScenarioManager.from_config(conf=config)
try:
    pass
except KeyError as e:
    print("Error in config file!")
    # Printing just the key
    print(e)
    # Printing the full error message
    sys.exit(1)
except ResponseException as e:
    print(e)
    sys.exit(1)

try:
    scenario_id = sys.argv[sys.argv.index("--scenario-id") + 1]
    load_generator = sm.simulations_dict[scenario_id].load_generator
except (KeyError, IndexError) as e:
    print("Provided scenario not found: " + str(e))
    sys.exit(1)

# Check if scenario_id is valid
if scenario_id not in sm.simulations_dict:
    print("Scenario " + str(scenario_id) + " not found.")
    sys.exit(1)

load_generator.execute_traffic()
result = sm.get_all_latencies()

print(json.dumps(result, indent=4, sort_keys=True))

# Check if --save-all is given from the command line
if "--save-all" in sys.argv:
    sm.save_all()
    print("Results saved successfully.")
