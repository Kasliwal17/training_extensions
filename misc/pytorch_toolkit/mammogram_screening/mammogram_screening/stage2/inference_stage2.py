import torch
from torch.utils.data import DataLoader
from sklearn.metrics import roc_auc_score
import numpy as np
import onnxruntime
from torchvision import transforms
from openvino.inference_engine import IECore
import os
from ..train_utils.dataloader import Stage2bDataset
from ..train_utils.models import Model2 as Model
from ..train_utils.get_config import get_config
import argparse

def to_numpy(tensor):
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()

class InferenceStage2():
    def __init__(self, test_loader, checkpoint, device):
        self.dataloder = test_loader
        self.checkpoint = checkpoint
        self.device = device

    def load_model(self, run_type='pytorch'):
        if run_type == 'onnx':
            model = onnxruntime.InferenceSession(self.checkpoint)
        elif run_type == 'pytorch':
            model = Model()
            checkpoint = torch.load(self.checkpoint, map_location=torch.device(self.device))
            model.load_state_dict(checkpoint['state_dict'])
            model.to(self.device)
            model.eval()
        else:
            ie = IECore()
            model_xml = os.path.splitext(self.checkpoint)[0] + ".xml"
            model_bin = os.path.splitext(model_xml)[0] + ".bin"
            model_temp = ie.read_network(model_xml, model_bin)
            model = ie.load_network(network=model_temp, device_name='CPU')
        return model

    def inference(self, model, run_type, out_nm):
        n = 0
        test_acc = 0.0
        arr_true = []
        arr_pred = []
        to_tensor = transforms.ToTensor()

        for  data in self.dataloder:
            X = data['bag'].float().to(self.device)[0].unsqueeze(1)
            y = data['cls'].float().to(self.device).unsqueeze(0)

            if run_type == 'pytorch':
                out = model(X)
                out = torch.sigmoid(out)
            elif run_type == "onnx":
                model = onnxruntime.InferenceSession(self.checkpoint)
                ort_inputs = {model.get_inputs()[0].name: to_numpy(X)}
                out = model.run(None, ort_inputs)
                out = np.array(out)
                out = to_tensor(out).to(self.device)
            else:
                out = model.infer(inputs={'input': X})['output']
                out = to_tensor(out)

            y_pred = out.data > 0.5
            y_pred = y_pred.float()

            arr_true.append(y.item())
            arr_pred.append(out.item())
            test_acc += torch.sum(y_pred == y.data).item()
            n += 1

        arr_true = np.array(arr_true).flatten()
        arr_pred = np.array(arr_pred).flatten()
        auc = roc_auc_score(arr_true, arr_pred)

        print('Test accuracy: '+str(test_acc/n)+'  test_auc: '+str(auc))
        results = {'label':arr_true,
                    'pred':arr_pred,
                    'test_acc':test_acc/n,
                    'test_auc':auc}
        np.save(out_nm, results)
        return test_acc/n, auc

def run_infer_stage2():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True, help='absolute path to config files', type=str)
    parser.add_argument('--runtype', required=True, help="Specify runtype ['pytorch','onnx','cpu']", type=str)
    args = parser.parse_args()

    config = get_config(action='inference', config_path=args.path, stage='stage2')
    num_workers = config['num_workers']

    if args.runtype == 'pytorch':
        checkpoint = config['checkpoint'] 
    else:
        checkpoint = config['onnx_checkpoint']

    if args.runtype == 'ir':
        device = 'cpu'
    else:
        gpu = config['gpu']
        device = 'cuda' if gpu else 'cpu'

    test_bags_path = config['test_bags_path']
    out_pred_np = config['out_pred_np']


    x_tst = np.load(test_bags_path, allow_pickle=True)

    tst_data = Stage2bDataset(x_tst, transform=None)
    tst_loader = DataLoader(tst_data, batch_size=1, shuffle=False, num_workers=num_workers)

    inference = InferenceStage2(test_loader=tst_loader, checkpoint=checkpoint, device=device)
    model = inference.load_model(run_type=args.runtype)
    test_acc, auc = inference.inference(model, run_type=args.runtype, out_nm=out_pred_np)
    print(f'Accuracy: {test_acc} | AUC:{auc}')

if __name__ == '__main__':

    run_infer_stage2()
