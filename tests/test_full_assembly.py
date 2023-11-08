"""
Tests for the full_assembly.py script
"""

import os
import sys
import unittest
from argparse import Namespace
from unittest.mock import patch


sys.path.append(os.path.abspath(
    os.path.join(os.path.realpath(__file__), '../../')
))

import full_assembly as App

TEST_OUTPUT = {'Summary':
                {'sample_1': 'pass',
                 'sample_2': 'fail'},
                'Details':
                {'sample_1':
                {'PCT_TARGET_BASES_20X': 
                    {'record':
                    [{'sample': 'sample_1',
                    'value': 99.0, 'status': 'pass'}]},
                    'Match_Sexes':
                    {'record':
                    [{'sample': 'sample_1',
                    'value': 'true', 'status': 'pass'}]},
                    'FOLD_ENRICHMENT':
                    {'record':
                    [{'sample': 'sample_1',
                    'value': 1500, 'status': 'pass'}]},
                    'percent_duplicates':
                    {'record':
                    [{'sample': 'sample_1_L001_R1',
                    'value': 44, 'status': 'pass'},
                    {'sample': 'sample_1_L001_R2',
                    'value': 42.74, 'status': 'pass'}]}},
                'sample_2':
                {'PCT_TARGET_BASES_20X':
                    {'record':
                    [{'sample': 'sample_2',
                    'value': 98.0, 'status': 'warn'}]},
                    'Match_Sexes':
                    {'record':
                    [{'sample': 'sample_2',
                        'value': 'false', 'status': 'fail'}]},
                    'FOLD_ENRICHMENT':
                    {'record':
                    [{'sample': 'sample_2',
                        'value': 1, 'status': 'fail'}]},
                    'percent_duplicates':
                    {'record':
                    [{'sample': 'sample_2_L001_R1',
                        'value': 41.32, 'status': 'pass'},
                    {'sample': 'sample_2_L001_R2',
                        'value': 43.3, 'status': 'pass'}]}}},
                'Thresholds':
                {'PCT_TARGET_BASES_20X':
                {'pass': [{'lt': 101}], 'warn': [{'eq': 98.0}, {'lt': 98.0}],
                    'fail': [{'eq': 95.0}, {'lt': 95.0}]},
                'METRIC.Recall_snp':
                {'pass': [{'eq': 1.0}], 'warn': [{'lt': 1.0}],
                    'fail': [{'lt': 0.99}]}, 
                'Match_Sexes':
                {True: [{'s_eq': 'yes'}], 'fail': [{'s_eq': 'no'}],
                    'warn': [{'s_eq': 'NA'}]},
                'FOLD_ENRICHMENT':
                {'pass': [{'gt': 1350}, {'lt': 1750}], 'warn': [{'eq': 1750}, {'gt': 1750}],
                    'fail': [{'lt': 1350}, {'eq': 1350}, {'eq': 1800}, {'gt': 1800}]},
                'percent_duplicates':
                {'pass': [{'lt': 45.0}], 'warn': [{'eq': 45.0},{'gt': 45.0}],
                    'fail': [{'eq': 50.0}, {'gt': 50.0}]}}}

class MainFunctionTest(unittest.TestCase):
    """
    Test the main function of full

    Args:
        unittest (_type_): _description_
    """
    maxDiff = None


    @patch('full_assembly.open')
    def test_main_function_alone(self, mock_open):
        """
        Testing the main function with no input
        "tests/testfiles/SampleSheet.csv", "tests/testfiles/multiqc_data.json", "tests/testfiles/CEN_multiqc_config_v2.1.0.yaml"
        """
        with patch('full_assembly.parse_args') as mock:
            args = Namespace()
            args.samplesheet = 'tests/testfiles/samplesheet_example.csv'
            args.data = 'tests/testfiles/multiqc_data_example.json'
            args.config = 'tests/testfiles/config_example.yaml'

            mock.return_value = args

            mock_open.return_value = mock.Mock()

            results = App.main()
            expected_output = TEST_OUTPUT
            self.assertEqual(results, expected_output,
                             "Main function does not output as expected")

    def test_main_function_no_input(self):
        """
        Test if code SystemExit is prompted when no inputs are given
        """
        with self.assertRaises(SystemExit) as context:
            App.main()
        self.assertEqual(str(context.exception), '2',
                         "Error message does not match")

if __name__=='__main__':
    unittest.main()
