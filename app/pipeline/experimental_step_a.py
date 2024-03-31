import json


class ExperimentalStepA:
    def __init__(self, step_config):
        self.json_file_path = step_config.get('input_json_path', "./service.bk.json")
        self.output_json_path = step_config.get('output_json_path', "./service.json")

    def execute(self):
        self.data = self.load_json_data()

