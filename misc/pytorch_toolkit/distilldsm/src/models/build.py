import os
import math
import torch
import torch.nn
from .UNetDistillDSM import U_Net

def fetch_model_by_name(model_name, *args, **kwargs):
    try:
        if "distill" in model_name.lower():
            print("******************* Distill DSM model *************************")
            return U_Net(img_ch = kwargs['n_features'],
                output_ch=kwargs['n_outputs'], conv_type='conv_2d',
                tsm=True, learn=True, tsm_length = kwargs['tsm_length'])
        elif "dsm" in model_name.lower():
            print("********************** DSM model ******************************")
            return U_Net(img_ch = kwargs['n_features'],
                output_ch=kwargs['n_outputs'], conv_type='conv_2d',
                tsm=True, learn=False, tsm_length = kwargs['tsm_length'])
        else:
            print("********************** 2D model *******************************")
            return U_Net(img_ch = kwargs['n_features'],
                output_ch=kwargs['n_outputs'], conv_type='conv_2d',
                tsm=False, learn=False, tsm_length = kwargs['tsm_length'])

    except AttributeError:
        raise ValueError("model name {} not supported".format(model_name))

def load_state_dict(model, state_dict, n_gpus, strict=False):
    try:
        if not strict:
            state_dict = match_state_dict_shapes(model.state_dict(), state_dict)
        model.load_state_dict(state_dict, strict=strict)
    except RuntimeError as error:
        if n_gpus > 1:
            if not strict:
                state_dict = match_state_dict_shapes(model.module.state_dict(), state_dict)
            model.module.load_state_dict(state_dict, strict=strict)
        else:
            raise error
    return model

def match_state_dict_shapes(fixed_state_dict, moving_state_dict):
    for key in fixed_state_dict:
        if key in moving_state_dict and fixed_state_dict[key].size() != moving_state_dict[key].size():
            moving_state_dict[key] = match_tensor_sizes(fixed_state_dict[key], moving_state_dict[key])
    return moving_state_dict


def match_tensor_sizes(fixed_tensor, moving_tensor):
    fixed_tensor_size = fixed_tensor.size()
    moving_tensor_size = moving_tensor.size()
    for dim in range(len(moving_tensor_size)):
        if fixed_tensor_size[dim] > moving_tensor_size[dim]:
            moving_tensor = torch.cat([moving_tensor] *
                                      int(math.ceil(fixed_tensor_size[dim] / moving_tensor_size[dim])),
                                      dim=dim)
        if fixed_tensor_size[dim] != moving_tensor_size[dim]:
            moving_tensor = moving_tensor.narrow(dim=dim, start=0, length=fixed_tensor_size[dim])
    return moving_tensor

def build_or_load_model(model_name, model_filename, n_features,
                            n_outputs, tsm_length=144, n_gpus=0, bias=None,
                            freeze_bias=False, strict=False, **kwargs):

    model = fetch_model_by_name(model_name,
                                    n_features=n_features, n_outputs=n_outputs,
                                    tsm_length=tsm_length, **kwargs)

    if bias is not None:
        model.fc.bias = torch.nn.Parameter(torch.from_numpy(bias))
    if freeze_bias:
        model.fc.bias.requires_grad_(False)
    if n_gpus > 1:
        model = model.cuda()
        model = torch.nn.DataParallel(model).cuda()
    elif n_gpus > 0:
        model = model.cuda()
    if os.path.exists(model_filename):
        state_dict = torch.load(model_filename)
        model = load_state_dict(model, state_dict, n_gpus=n_gpus, strict=strict)
    return model
