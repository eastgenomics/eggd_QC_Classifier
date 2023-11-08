"""
We have all the functions needed to generate the individual 
outputs that we need, all we have to do is join everything together in
a complex dictionary. 

All inputs:
    - SampleSheet.csv
    - multiqc_data.json
    - config.yaml file

Output structure:
{
    {
    "Summary":{
        "SampleID_1": "pass", 
        "SampleID_2": "warn"

    },
   "Details":{
       "SampleID_1":{
            "Metric_1":{
                "record":[
                    {
                    "sample":"SampleID_1_R1",
                    "value": 1.0,
                    "status": "pass"
                    },
                    {
                    "sample":"SampleID_1_R1",
                    "value": 1.0,
                    "status": "pass"
                    }
                ]
            }
        }
    }.
    "Thresholds":{
        "Metric_1 :  "json like structure from config file"
    }
}

"""
import argparse
import json
import bin.utils as Classifier

def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments

    Returns:
        args : Namespace
          Namespace of passed command line argument inputs
    """
    parser = argparse.ArgumentParser(description='QC Classifier for multiqc data')

    parser.add_argument('samplesheet', type=str,
                        help='filepath to SampleSheet.csv file')
    parser.add_argument('data', type=str,
                        help='filepath to multiqc.json file')
    parser.add_argument('config', type=str,
                        help='filepath to config.yaml file')
    args = parser.parse_args()

    return args


def main():
    """
    Main entry point to run all functions
    """
    args = parse_args()
    # List of samples
    sample_list = Classifier.get_sample_lists(args.samplesheet)

    # Multiqc data
    multiqc_data = Classifier.get_multiqc_data(args.data)

    # List of config_fields
    yaml_content = Classifier.read_config(args.config)
    config_fields = list(yaml_content["table_cond_formatting_rules"].keys())

    summary_report_output = {}
    details_report_output = {}

    for sample in sample_list:
        metrics_summary = {}
        status_list = []
        for config_field in config_fields:
            header_id = Classifier.map_header_id(config_field)
            parameters = Classifier.get_unique_parameters(config_field,
                                                          yaml_content)
            key_values = Classifier.get_key_value(multiqc_data,
                                                  sample,
                                                  header_id)

            if key_values:
                record = []
                for key_value in key_values:
                    key = key_value
                    value = key_values[key]
                    status = Classifier.get_status(value, parameters)
                    record_call = {
                                    "sample": key,
                                    "value": value,
                                    "status": status
                                  }
                    record.append(record_call)
                    status_list.append(status)

                record = {
                          header_id:{
                                     "record": record
                                    }
                         }
                metrics_summary.update(record)

        if 'fail' in status_list:
            status_summary = 'fail'
        elif 'warn' in status_list:
            status_summary = 'warn'
        else:
            status_summary = 'pass'

        summary_report_output.update({sample:status_summary})
        details_report_output.update({sample:metrics_summary})

    # Generate structure of thresholds report
    thresholds_report_output = {}
    for config_field in config_fields:
        header_id = Classifier.map_header_id(config_field)
        parameters = Classifier.get_unique_parameters(config_field,
                                                      yaml_content)
        thresholds_report_output.update({header_id: parameters})

    # Generating qc_report structure
    qc_report_output = {"Summary":summary_report_output}
    qc_report_output.update({"Details": details_report_output})
    qc_report_output.update({"Thresholds": thresholds_report_output})
    qc_report_filename = Classifier.get_output_filename(multiqc_data)

    # Saving output
    with open(qc_report_filename, 'w', encoding='UTF-8') as output_filename:
        json.dump(qc_report_output, output_filename, indent="   ")

    return qc_report_output

if __name__ == "__main__":
    main()
