import unittest
import os
import numpy as np
import torch
import torchvision
from torch.backends import cudnn
from utils import get_config
from utils import download_checkpoint, download_data
from utils.model import Encoder, Decoder, AutoEncoder
from torch.utils.data import DataLoader
from utils.data_loader import CustomDatasetPhase1, CustomDatasetPhase2
from utils.train_utils import validate_model_phase1
from termcolor import colored
import json
import random

from utils.model import AutoEncoder, Decoder
from utils.evaluators import compare_psnr_batch, compare_ssim_batch
cudnn.benchmark = True


def load_model(eff_flag=False, it_no=0, alpha=1, beta=1, depth=3, width=64, phase=1):
    if phase == 1:
        if eff_flag:
            model = AutoEncoder(
                (alpha[it_no]*depth).astype(int), (beta[it_no]*width).astype(int))
        else:
            model = AutoEncoder(int(alpha*depth), int(beta*width))
    else:
        if eff_flag:
            model = Decoder((alpha[it_no]*depth).astype(int),
                            (beta[it_no]*width).astype(int))
        else:
            model = Decoder(int(alpha*depth), int(beta*width))

    return model


# validate_model_phase1(config, test_dataloader, model, msecrit)


def create_train_test_for_densenet121():
    class TrainerTest(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            config = get_config(action='train')
            cls.config = config
            if os.path.exists(config["default_image_path"]):
                image_path = config["default_image_path"]
            else:
                if not os.path.exists(config["image_path"]):
                    download_data()
                image_path = config["image_path"]

            dataset_train = RSNADataSet(
                cls.config['dummy_train_list'],
                cls.config['dummy_labels'],
                image_path, transform=True)
            dataset_valid = RSNADataSet(
                cls.config['dummy_valid_list'],
                cls.config['dummy_labels'],
                image_path, transform=True)
            dataset_test = RSNADataSet(
                cls.config['dummy_test_list'],
                cls.config['dummy_labels'],
                image_path, transform=True)
            cls.data_loader_train = DataLoader(
                dataset=dataset_train,
                shuffle=True,
                pin_memory=False)
            cls.data_loader_valid = DataLoader(
                dataset=dataset_valid,
                shuffle=False,
                pin_memory=False)
            cls.data_loader_test = DataLoader(
                dataset=dataset_test,
                shuffle=False,
                pin_memory=False)

        def test_config(self):
            self.assertGreaterEqual(self.config["lr"], 1e-8)
            self.assertEqual(self.config["clscount"], 3)

        def test_trainer(self):
            self.model = DenseNet121(self.config["clscount"])
            if not os.path.exists(self.config["checkpoint"]):
                download_checkpoint()
            self.device = self.config["device"]
            self.trainer = RSNATrainer(
                self.model, self.data_loader_train,
                self.data_loader_valid, self.data_loader_test,
                self.config["clscount"], self.config["checkpoint"],
                self.device, self.config["class_names"], self.config["lr"])
            self.trainer.train(
                self.config["max_epoch"], self.config["savepath"])
            cur_train_loss = self.trainer.current_train_loss
            self.trainer.train(
                self.config["max_epoch"], self.config["savepath"])
            self.assertLessEqual(
                self.trainer.current_train_loss, cur_train_loss)

    return TrainerTest


def create_train_test_for_densenet121eff():
    class TrainerTestEff(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            config = get_config(action='train', optimised=True)
            cls.config = config
            if os.path.exists(config["default_image_path"]):
                image_path = config["default_image_path"]
            else:
                if not os.path.exists(config["image_path"]):
                    download_data()
                image_path = config["image_path"]

            dataset_train = RSNADataSet(
                cls.config['dummy_train_list'],
                cls.config['dummy_labels'],
                image_path, transform=True)
            dataset_valid = RSNADataSet(
                cls.config['dummy_valid_list'],
                cls.config['dummy_labels'],
                image_path, transform=True)
            dataset_test = RSNADataSet(
                cls.config['dummy_test_list'],
                cls.config['dummy_labels'],
                image_path, transform=True)
            cls.data_loader_train = DataLoader(
                dataset=dataset_train,
                shuffle=True,
                pin_memory=False)
            cls.data_loader_valid = DataLoader(
                dataset=dataset_valid,
                shuffle=False,
                pin_memory=False)
            cls.data_loader_test = DataLoader(
                dataset=dataset_test,
                shuffle=False,
                pin_memory=False)

        def test_trainer(self):
            alpha = self.config['alpha'] ** self.config['phi']
            beta = self.config['beta'] ** self.config['phi']
            self.model = DenseNet121Eff(
                alpha, beta, self.config['class_count'])
            if not os.path.exists(self.config["checkpoint"]):
                download_checkpoint()
            self.device = self.config["device"]
            self.trainer = RSNATrainer(
                self.model, self.data_loader_train,
                self.data_loader_valid, self.data_loader_test,
                self.config["class_count"], self.config["checkpoint"],
                self.device, self.config["class_names"], self.config["lr"])
            self.trainer.train(
                self.config["max_epoch"], self.config["savepath"])
            cur_train_loss = self.trainer.current_train_loss
            self.trainer.train(
                self.config["max_epoch"], self.config["savepath"])
            self.assertLessEqual(
                self.trainer.current_train_loss, cur_train_loss)

        def test_config(self):
            self.config = get_config(action='train', optimised=True)
            self.learn_rate = self.config["lr"]
            self.class_count = self.config["class_count"]
            self.assertGreaterEqual(self.learn_rate, 1e-8)
            self.assertEqual(self.class_count, 3)
            self.assertGreaterEqual(self.config['alpha'], 0)
            self.assertGreaterEqual(self.config['phi'], -1)
            self.assertLessEqual(self.config['alpha'], 2)
            self.assertLessEqual(self.config['phi'], 1)
    return TrainerTestEff


class TestTrainer(create_train_test_for_densenet121()):
    'Test case for DenseNet121'


class TestTrainerEff(create_train_test_for_densenet121eff()):
    'Test case for DenseNet121Eff'


if __name__ == '__main__':

    unittest.main()
