import unittest
import os
import json
from tools.train import RSNATrainer
from utils.dataloader import RSNADataSet
from torch.utils.data import DataLoader
from utils.model import DenseNet121
import numpy as np

def get_config(optimised=False):
    path = os.path.dirname(os.path.realpath(__file__))
    with open(path+'/test_config.json','r') as f1:
        config_file = json.load(f1)
    
    if optimised:
        return config_file['train_eff']
    else:
        return config_file['train']


class TrainerTest(unittest.TestCase):
    config = get_config()
    class_count = config["clscount"]
    image_path = config["imgpath"]
    np_path = config["npypath"]
    learn_rate = config["lr"]
    tr_list = config["dummy_train_list"]
    tr_labels = config["dummy_train_labels"]
    val_list = config["dummy_valid_list"]
    val_labels = config["dummy_valid_labels"]
    test_list = config["dummy_test_list"]
    test_labels = config["dummy_test_labels"]

    dataset_train = RSNADataSet(tr_list, tr_labels, image_path, transform=True)
    dataset_valid = RSNADataSet(val_list, val_labels, image_path, transform=True) 
    dataset_test = RSNADataSet(test_list, test_labels, image_path, transform=True)

    data_loader_train = DataLoader(dataset=dataset_train, batch_size=2, shuffle=True,  num_workers=4, pin_memory=False)
    data_loader_valid = DataLoader(dataset=dataset_valid, batch_size=2, shuffle=False, num_workers=4, pin_memory=False)
    data_loader_test = DataLoader(dataset=dataset_test, batch_size=1, shuffle=False,  num_workers=4, pin_memory=False)

        
    def test_paths(self):

        self.assertTrue(os.path.exists(self.image_path))
        self.assertTrue(os.path.exists(self.np_path+'train_list.npy'))
        self.assertTrue(os.path.exists(self.np_path+'train_labels.npy'))
        self.assertTrue(os.path.exists(self.np_path+'valid_list.npy'))
        self.assertTrue(os.path.exists(self.np_path+'valid_labels.npy'))
        self.assertTrue(os.path.exists(self.np_path+'test_list.npy'))
        self.assertTrue(os.path.exists(self.np_path+'test_labels.npy'))

    def test_config(self):

        self.assertGreaterEqual(self.learn_rate,1e-8)
        self.assertEqual(self.class_count,3)

    def test_trainer(self):

        self.model = DenseNet121(self.class_count)
        self.class_names = self.config["class_names"]
        self.checkpoint = self.config["checkpoint"]
        self.device = self.config["device"]
        self.trainer = RSNATrainer(self.model, self.data_loader_train, 
        self.data_loader_valid, self.data_loader_test, 
        self.class_count,self.checkpoint, self.device, self.class_names)
        self.trainer.train(max_epoch, timestamp_launch, lr)
        cur_train_loss = self.trainer.current_train_loss
        cur_valid_loss = self.trainer.current_valid_loss
        self.trainer.train()
        self.assertLessEqual(self.trainer.current_train_loss, cur_train_loss)
        self.assertLessEqual(self.trainer.current_valid_loss, cur_valid_loss)

    def test_config_eff(self):
        self.config = get_config()
        self.learn_rate = self.config["lr"]
        self.class_count = self.config["clscount"]
        self.assertGreaterEqual(self.learn_rate,1e-8)
        self.assertEqual(self.class_count,3)
        self.assertGreaterEqual(self.config['alpha'],0)
        self.assertGreaterEqual(self.config['phi'],0)
        self.assertLessEqual(self.config['alpha'],2)
        self.assertLessEqual(self.config['phi'],1)


if __name__ == '__main__':

    unittest.main()

        




