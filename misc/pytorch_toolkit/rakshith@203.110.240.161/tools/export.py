import os
import json
from utils.exporter import Exporter
import argparse

def _get_config_():
    path = os.path.dirname(os.path.realpath(__file__))
    with open(path+'/export_config.json','r') as f1:
        config_file = json.load(f1)

    return config_file

def export(args):

    export_config = _get_config_()
    exporter = Exporter(export_config)

    if args.onnx:
        exporter.export_model_onnx()
    if args.ir:
        exporter.export_model_ir()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--onnx",required=False, help="Set to True, if you wish to export onnx model",default=True,type = bool)
    parser.add_argument("--ir",required=False, help="Set to True, if you wish to export IR",default=True,type = bool)

    args = parser.parse_args()

    export(args)

