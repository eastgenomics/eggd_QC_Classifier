"""
Personal set of functions which are used to complete some of the main steps for QC classification

Functions:
- map_header_id(config_field): 
    - Function that gives the Header ID for any give Unique ID.
- reade_config(yaml_file): 
    - Function that reads any .yaml file in a .json-like structure.
- get_unique_parameters(unique_id, yaml_file): 
    - Function  that outputs the list of conditions/parameters found in the config.yaml file.
- get_sample_lists(csv_filepath):
    - Creates a structured list of samples from the provided SampleSheet.csv.
- get_multiqc_data(multiqc_filepath):
    - Return a flattened dictionary with values for all samples from given multiqc run.
- get_key_value(summarised_data, sample_id, header_id):
    - Return the value of given sample_id and header_id in a dictionary format.
- get_status(value, parameters):
    - Function to determine pass/warn/fail status based on given value and parameters.

Python version 3.10.12 
"""
import json
from pathlib import Path
import re
from flatten_json import flatten
import pandas
import yaml


def map_header_id(config_field) -> str:
    """ Function that gives the Header ID for any give Unique ID.
    IMPORTANT: file "idConfigFieldRelationship.json" in "resources/"should be 
    included to work.

    Args:
        config_field (str): field provided by the config.yaml file, in
        "table_cond_formatting rules"

    Returns:
        str: Header ID, it is the associated metric used in the multiqc.json file
    """
    # First get file from resources/ folder
    config_header_filepath = Path(__file__).parent.joinpath('..','resources',
                                                            'idConfigFieldRelationship.json')
    with open(config_header_filepath,
              'r', encoding='UTF-8') as file:
        config_field_relationship = json.load(file)
    id_mapping = {item["Config_field"]: item["Header_ID"] for item in config_field_relationship}
    header_id = id_mapping.get(config_field)

    if header_id is None:
        raise NameError("Missing Header ID for config field: " + config_field)

    return header_id


def read_config(yaml_file) -> dict:
    """Function that reads any .yaml file in a .json-like structure.

    Args:
        yaml_file (str): filename and relative path of the config.yaml file
    Output:
        - yaml_contents (dictionary): contents of config.yaml file
    """
    with open(yaml_file, 'r', encoding='UTF-8') as file:
        yaml_file = yaml.safe_load(file)

    if not yaml_file.get("table_cond_formatting_rules"):
        raise TypeError(f"{yaml_file} does not have "
                        + "'table_cond_formatting_rules' key")

    return yaml_file


def get_unique_parameters(unique_id, yaml_file) -> dict:
    """Function  that outputs the list of conditions/parameters found in the config.yaml file.

    Input:
        - Config field (str): fields found in table_cond_formatting_rules from the "config.yaml"
                              file.
        - Output from read_config('config.yaml') function.

    Output:
        - parameters (dictionary): Conditions for the given config field.

    """

    return yaml_file["table_cond_formatting_rules"][unique_id]


def get_sample_lists(csv_filepath) -> list:
    """Creates a structured list of samples from the provided SampleSheet.csv.

    Args:
        csv_filepath (str): filelocation of csv_filepath

    Returns:
        list: list of strings, each string represents a sample from multiqc.json 
    """

    # Get all IDs from sample sheet
    with open(csv_filepath, 'r', encoding='UTF-8') as file:
        sample_sheet = pandas.read_csv(file, header=None, usecols=[0])
    column = sample_sheet[0].tolist()
    sample_list = column[column.index('Sample_ID') + 1:]

    return sample_list


def get_multiqc_data(multiqc_filepath) -> dict:
    """Return a flattened dictionary with values for all samples from given multiqc run.

    Args:
        multiqc_filepath (str): filepath for where multiqc_file is located

    Returns:
        dict: dictionary of summarised multiqc.json file
    """
    with open(multiqc_filepath, 'r', encoding='UTF-8') as file:
        multiqc_data = json.load(file)

        data = flatten(multiqc_data, '.',
                       root_keys_to_ignore = {'report_data_sources',
                                              'report_general_stats_headers',
                                              'reports_plot_data'})
    return data


def get_key_value(summarised_data, sample_id, header_id):
    """Return the value of given sample ID and header_id in a dictionary format.

    Args:
        summarised_data (dict): multiqc_data obtained from get_multiqc_data().
        sample_id (str): Sample ID obtained from SampleSheet.csv
        header_id (str): Metric used in multiqc.json file, obtained from 
                         output map_header_id(config_field)

    Returns:
        dict: dictionary with following structure {"multiqc_sample_ID" : "value"}, 
        may return more than one value.
    """
    # return all values for a given sampleID
    result = {}
    for key, val in summarised_data.items():
        if sample_id in key and header_id in key:
            if f"{sample_id}.{header_id}" in key:
                new_key = re.search(f"{sample_id}", key)
            else:
                new_key = re.search(f"{sample_id}[A-Z0-9_]+", key)

            # Exception created for "PCT_TARGET_BASES_20X"
            if header_id == "PCT_TARGET_BASES_20X":
                val = val*100

            if new_key:
                new_key = new_key.group()
                result.update({new_key:val})

    return result


def get_status(value, parameters):
    """Function to determine pass/warn/fail status based on given value and parameters.

    Inputs:
        Value (string or float)
        Parameters (dictionary of parameters from function getUniqueParameters)

    Output:
        Status: string with one of the following options:
                   "unknown", "pass", "warn" or "fail" 
                Status "unknown" should be avoided.
    """

    status = "unknown" # Given default status if not classified

    # Iterate through possible status values i.e: pass-or-true/warn/fail
    for possible_status in list(parameters.keys()):

        conditions = parameters.get(possible_status)

        # Iterate through the list of conditions for each possible status: 'gt', 'lt', 'eq', 's_eq'
        for condition in conditions:

            # Checking if any of the following conditions exist
            # The "or statements" are necessary to prevent any condition with value
            # 0 to be treated as false
            if condition.get('gt') or condition.get('gt') == 0:
                if float(value) > float(condition.get('gt')):
                    status = possible_status

            if condition.get('lt') or condition.get('lt') == 0:
                if float(value) < float(condition['lt']):
                    status = possible_status

            if condition.get('eq') or condition.get('eq') == 0:
                if float(value) == float(condition['eq']):
                    status = possible_status

            if condition.get('s_eq'):
                if str(value) == str(condition['s_eq']):
                    status = possible_status

        # Config field "Match_Sexes" may return value as a string "false" or "true"
        # which is different to what is set for the config fields.
    if value in ["true", "pass"]:
        status = "pass"

    if value in ["unknown", "warn"]:
        status = "warn"

    if value in ["false", "fail"]:
        status = "fail"

    return status # Returns the determined status


def get_output_filename(summarised_data):
    """Generate output filename for QC classifier from the multiqc data.

    Args:
        summarised_data (dict): multiqc_data obtained from get_multiqc_data().

    Returns:
        str: proposed filename for the QC report output e.g.: 
        200222_A12345_1234_ABCDEFGHI5_RUN-RUN-200221_6789-multiqc.json
    """
    match = re.search("[0-9]{6}_[A-Z0-9]{6}_[0-9]{4}_[A-Z0-9a-z_-]+multiqc",
                                summarised_data["report_multiqc_command"])

    if match:
        return f"{match.group()}.json"
    else:
        print(
            "Run ID could not be parsed from 'report_multiqc_command' field in multiqc json:\n"
            f"{summarised_data['report_multiqc_command']}. \n"
            "Writing to multiqc_qc_classified.json"
            )
    return 'multiqc_qc_classified.json'
