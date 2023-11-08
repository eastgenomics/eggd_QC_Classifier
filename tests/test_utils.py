"""
Tests for general functions in bin/utils.py
"""

import os
import sys
import unittest
from unittest.mock import patch


sys.path.append(os.path.abspath(
    os.path.join(os.path.realpath(__file__), '../../')
))

import bin.utils as Classifier

TEST_DATA_DIR = (
    os.path.join(os.path.dirname(__file__), 'testfiles')
)

TEST_YAML_CONTENT = {'title': 'East GLH MultiQC Report',
                     'subtitle': 'Cancer Endocrine Neurology',
                     'table_cond_formatting_rules': 
                        {'mqc-generalstats-picard-PCT_TARGET_BASES_20X':
                            {'pass':[{'lt': 101}],
                             'warn': [{'eq': 98.0}, {'lt': 98.0}],
                             'fail': [{'eq': 95.0}, {'lt': 95.0}]},
                         'METRIC_Recall_snp':
                             {'pass': [{'eq': 1.0}],
                              'warn': [{'lt': 1.0}],
                              'fail': [{'lt': 0.99}]},
                         'Match_Sexes':
                            {True: [{'s_eq': 'yes'}],
                             'fail': [{'s_eq': 'no'}],
                             'warn': [{'s_eq': 'NA'}]},
                         'FOLD_ENRICHMENT': 
                                {'pass': [{'gt': 1350}, {'lt': 1750}],
                                 'warn': [{'eq': 1750}, {'gt': 1750}],
                                 'fail': [{'lt': 1350}, {'eq': 1350},
                                          {'eq': 1800}, {'gt': 1800}]},
                         'mqc-generalstats-fastqc-percent_duplicates':
                                {'pass': [{'lt': 45.0}],
                                 'warn': [{'eq': 45.0}, {'gt': 45.0}],
                                 'fail': [{'eq': 50.0}, {'gt': 50.0}]}}}

TEST_MULTIQC_DATA = {
    'report_general_stats_data.0.sample_1.FOLD_ENRICHMENT': 1500,
    'report_general_stats_data.0.sample_2.FOLD_ENRICHMENT': 1,
    'report_general_stats_data.0.sample_1.PCT_TARGET_BASES_20X': 0.99,
    'report_general_stats_data.0.sample_2.PCT_TARGET_BASES_20X': 0.98,
    'report_general_stats_data.1.sample_1.Match_Sexes': 'true',
    'report_general_stats_data.1.sample_2.Match_Sexes': 'false',
    'report_saved_raw_data.multiqc_happy_snp_data.sample_1_SNP_ALL.Metric.Recall_snp': '1.0',
    'report_saved_raw_data.multiqc_happy_snp_data.sample_1_SNP_PASS.Metric.Recall_snp': '1.0',
    'report_saved_raw_data.multiqc_general_stats.sample_1_L001_R1.percent_duplicates': 44,
    'report_saved_raw_data.multiqc_general_stats.sample_1_L001_R2.percent_duplicates': 42.74,
    'report_saved_raw_data.multiqc_general_stats.sample_2_L001_R1.percent_duplicates': 41.32,
    'report_saved_raw_data.multiqc_general_stats.sample_2_L001_R2.percent_duplicates': 43.30,
    'report_multiqc_command': 'multiqc 230620_A01234_5678_ABCDEFGHI9_ABC-ABC-230620_1234-multiqc.html'}

class TestMapHeaderID(unittest.TestCase):
    """
    Tests for Classifier.map_header_id(config_field)
    """
    test_inputs = [
                   'mqc-generalstats-picard-PCT_TARGET_BASES_20X',
                   'METRIC_Recall_snp',
                   'Match_Sexes',
                   'FOLD_ENRICHMENT',
                   'mqc-generalstats-fastqc-percent_duplicates'
                    ]

    def test_map_header_id(self):
        """
        Testing if given config fields from test_inputs outputs the right
        list of expected header_ids
        """
        expected_outputs = [
                            'PCT_TARGET_BASES_20X',
                            'METRIC.Recall_snp',
                            'Match_Sexes',
                            'FOLD_ENRICHMENT',
                            'percent_duplicates'
                            ]
        output_list = []
        for config_field in self.test_inputs:
            output_list.append(Classifier.map_header_id(config_field))
        self.assertEqual(output_list, expected_outputs,
                         "Expected outputs not the same")

    def test_not_found_map_header_id(self):
        """
        Test if given config field is not found
        """
        with self.assertRaises(NameError) as context:
            Classifier.map_header_id("unknown_field")
        self.assertEqual(str(context.exception),
                         "Missing Header ID for config field: unknown_field",
                         "Error message does not match")


class TestReadConfig(unittest.TestCase):
    """
    Tests for read_config(yaml_file)
    """
    CONFIG_EXAMPLE_FILEPATH = os.path.join(TEST_DATA_DIR,
                                           'config_example.yaml')

    def test_reading_file(self):
        """
        Testing if the file opens as expected
        """
        tested_output = Classifier.read_config(self.CONFIG_EXAMPLE_FILEPATH)
        self.assertEqual(tested_output, TEST_YAML_CONTENT,
                         "The example config_example.yaml "
                         + "file is not read as expected")

    def test_file_not_found(self):
        """
        Testing if FileNotFound error is raised if config file not found
        """
        unknown_filepath = os.path.join(TEST_DATA_DIR, 'unknown.yaml')
        with self.assertRaises(FileNotFoundError,
                               msg="FileNotFoundError not given"):
            Classifier.read_config(unknown_filepath)

    @patch('bin.utils.yaml.safe_load',
           lambda yaml_file: TEST_YAML_CONTENT.fromkeys(('title',
                                                         'subtitle')))
    def test_invalid_yaml_file(self):
        """
        Testing if the TypeError is raised when given yaml file does not
        have key with config fields.
        """
        with self.assertRaises(TypeError, msg="TypeError not given"):
            Classifier.read_config(self.CONFIG_EXAMPLE_FILEPATH)


class TesGettUniqueParameters(unittest.TestCase):
    """
    Tests for get_unique_parameters(unique_id, yaml_file)
    """

    def test_real_config_field(self):
        """
        Test if a real config field outputs as expected.
        """
        example_config_field = 'FOLD_ENRICHMENT'
        tested_output = Classifier.get_unique_parameters("FOLD_ENRICHMENT",
                                                         TEST_YAML_CONTENT)
        self.assertEqual(tested_output,
                         TEST_YAML_CONTENT['table_cond_formatting_rules']
                                          [example_config_field])


class TestGetSampleLists(unittest.TestCase):
    """
    Test for get_sample_list(csv_filepath):
    """
    SAMPLESHEET_EXAMPLE_FILEPATH = os.path.join(TEST_DATA_DIR,
                                                'samplesheet_example.csv')

    def test_reading_file(self):
        """
        Test if samplesheet.csv file is read as expected
        """
        expected_output = ['sample_1', 'sample_2']
        tested_output = Classifier.get_sample_lists(self.SAMPLESHEET_EXAMPLE_FILEPATH)
        self.assertEqual(tested_output, expected_output,
                         "The samplesheet_example.csv is not read as expected")

    def test_file_not_found(self):
        """
        Testing if FileNotFound error is raised if config file not found
        """
        unknown_filepath = os.path.join(TEST_DATA_DIR, 'unknown.csv')
        with self.assertRaises(FileNotFoundError,
                               msg="FileNotFoundError not given"):
            Classifier.read_config(unknown_filepath)


class TestGetMultiqcData(unittest.TestCase):
    """
    Tests for get_multiqc_data(multiqc_filepath)
    """
    MULTIQC_EXAMPLE_FILEPATH = os.path.join(TEST_DATA_DIR,
                                            'multiqc_data_example.json')

    def test_reading_file(self):
        """
        Test if multiqc_data.csv is read as expected
        """
        expected_output = TEST_MULTIQC_DATA
        tested_output = Classifier.get_multiqc_data(self.MULTIQC_EXAMPLE_FILEPATH)
        self.assertEqual(tested_output, expected_output,
                         "The multiqc_data_example.json is not read as expected")

    def test_ignore_keys(self):
        """
        Test if keys are ignored using the flatten funciton
        """
        with patch('bin.utils.json.load') as mock:

            mock.return_value = {'report_data_sources':'should_ignore',
                                 'report_general_stats_headers':'should_ignore',
                                 'reports_general_stats_data':
                                    {'example':'should_retain'},
                                 'reports_plot_data':'should_ignore'}

            expected_output = {'reports_general_stats_data.example':'should_retain'}
            tested_output = Classifier.get_multiqc_data(self.MULTIQC_EXAMPLE_FILEPATH)
            self.assertEqual(tested_output,expected_output,
                             "The get_multiqc_data function " 
                             + "does not ignore keys as expected")      


class TestGetKeyValue(unittest.TestCase):
    """
    Tests for function get_key_value(summarised_data, sample_id, header_id)
    """

    def test_standard_inputs(self):
        """
        Test the function with standard inputs
        """
        tested_output = Classifier.get_key_value(TEST_MULTIQC_DATA,
                                                 'sample_1', 'FOLD_ENRICHMENT')
        expected_output = {'sample_1': 1500}
        self.assertEqual(tested_output, expected_output,
                        "The output of get_key_value function with standard "
                        + "inputs is not expected")

    def test_exception(self):
        """
        Test the function when header "PCT_TARGET_BASES_20X is processed as expected
        """
        tested_output = Classifier.get_key_value(TEST_MULTIQC_DATA,'sample_1',
                                                'PCT_TARGET_BASES_20X')
        expected_output = {'sample_1': 99}
        self.assertEqual(tested_output, expected_output,
                        "The output of get_key_value function using the "
                        + "exception is not expected")

    def test_reads_data(self):
        """
        Test the function when a given header ID is associated with Reads data.
        """
        tested_output = Classifier.get_key_value(TEST_MULTIQC_DATA,'sample_1',
                                                'percent_duplicates')
        expected_output = {'sample_1_L001_R1': 44,
                           'sample_1_L001_R2': 42.74}
        self.assertEqual(tested_output, expected_output,
                        "The output of using 'percent_duplicates' is not expected")

    def test_controls_data(self):
        """
        Test the function when a given header ID is associated with the 
        control data.
        """
        tested_output = Classifier.get_key_value(TEST_MULTIQC_DATA,'sample_1',
                                                'Metric.Recall_snp')
        expected_output = {'sample_1_SNP_ALL': '1.0', 'sample_1_SNP_PASS':'1.0'}
        self.assertEqual(tested_output, expected_output,
                        "The output of using 'Metric.Recall_snp'"
                        + "is not expected")

    def test_unfound_query(self):
        """
        Test the function when data from the given header ID 
        does not exist on given sample
        """
        tested_output = Classifier.get_key_value(TEST_MULTIQC_DATA,'sample_12',
                                                'Metric.Recall_snp')
        expected_output = {}
        self.assertEqual(tested_output, expected_output,
                        "The output of an unfound query isnot  an empty dictionary")


class TestGetStatus(unittest.TestCase):
    """
    Tests for function get_status(value, parameters)
    """
    def test_float_values(self):
        """
        Example inputs, testing the charade of if statements with 
        conditions 'gt' 'lt' 'eq'
        """
        tested_values = [1351,1749,1750,1799,1350,1800,0,1900]
        expected_outcomes = ['pass', 'pass', 'warn', 'warn',
                             'fail', 'fail', 'fail', 'fail']
        parameters = TEST_YAML_CONTENT['table_cond_formatting_rules']['FOLD_ENRICHMENT']
        output_list = []
        for value in tested_values:
            output = Classifier.get_status(value, parameters)
            output_list.append(output)

        self.assertEqual(output_list, expected_outcomes,
                         "The output of get_status with float numbers is not expected.")

    def test_string_values(self):
        """
        Example inputs, testing if statement with 's_eq' conditions
        """
        tested_values = ["yes","no","NA","maybe"]
        expected_outcomes = [True,"fail","warn","unknown"]
        parameters = TEST_YAML_CONTENT['table_cond_formatting_rules']['Match_Sexes']
        output_list = []
        for value in tested_values:
            output = Classifier.get_status(value, parameters)
            output_list.append(output)

        self.assertEqual(output_list, expected_outcomes,
                        "The output of get_status with str values is not expected.")

    def test_preset_strings(self):
        """
        Test function with input strings that which do not require parameters.
        """
        tested_values = ['true','pass','unknown','warn','false','fail','']
        expected_outcomes = ['pass','pass','warn','warn',
                             'fail','fail','unknown']
        output_list = []
        for value in tested_values:
            output = Classifier.get_status(value, {})
            output_list.append(output)

        self.assertEqual(output_list, expected_outcomes,
                         "The output of get_status with preset str values is not expected.")


class TestGetOutputFilename(unittest.TestCase):
    """
    Tests for function get_output_filename(summarised_data)
    """
    def test_expected_filename(self):
        """
        Test function with summary data which includes the 
        "report_multiqc_command" key
        """
        tested_output = Classifier.get_output_filename(TEST_MULTIQC_DATA)
        expected_output = '230620_A01234_5678_ABCDEFGHI9_ABC-ABC-230620_1234-multiqc.json'
        self.assertEqual(tested_output, expected_output,
                        "The output of get_output_filename is expected.")

    def test_unfound_filename(self):
        """
        Test whether standard filename is given if pattern in 
        "report_multiqc_command" key not found
        """
        tested_output = Classifier.get_output_filename({'report_multiqc_command':''})
        expected_output = 'multiqc_qc_classified.json'
        self.assertEqual(tested_output, expected_output,
                        "The output of get_output_filename is expected.")

if __name__=='__main__':
    unittest.main()
