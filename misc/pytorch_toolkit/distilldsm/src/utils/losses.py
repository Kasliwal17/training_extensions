import torch

def compute_per_channel_dice(input, target, epsilon=1e-6, weight=None):
    """
    Computes DiceCoefficient as defined in https://arxiv.org/abs/1606.04797 given  a multi channel input and target.
    Assumes the input is a normalized probability, e.g. a result of Sigmoid or Softmax function.
    Source: wolny's GitHub project: https://github.com/wolny/pytorch-3dunet
    Args:
         input (torch.Tensor): NxCxSpatial input tensor
         target (torch.Tensor): NxCxSpatial target tensor
         epsilon (float): prevents division by zero
         weight (torch.Tensor): Cx1 tensor of weight per channel/class
    """

    # input and target shapes must match
    assert input.size() == target.size(), "'input' ({}) and 'target' ({}) must have the same shape".format(
        input.size(), target.size())

    input = flatten(input)
    target = flatten(target)
    target = target.float()

    # compute per channel Dice Coefficient
    intersect = (input * target).sum(-1)
    if weight is not None:
        intersect = weight * intersect

    # here we can use standard dice (input + target).sum(-1) or extension (see V-Net) (input^2 + target^2).sum(-1)
    denominator = (input * input).sum(-1) + (target * target).sum(-1)
    return 2 * (intersect / denominator.clamp(min=epsilon))


def flatten(tensor):
    """Flattens a given tensor such that the channel axis is first.
    The shapes are transformed as follows:
       (N, C, D, H, W) -> (C, N * D * H * W)
    """
    # number of channels
    C = tensor.size(1)
    # new axis order
    axis_order = (1, 0) + tuple(range(2, tensor.dim()))
    # Transpose: (N, C, D, H, W) -> (C, N, D, H, W)
    transposed = tensor.permute(axis_order)
    # Flatten: (C, N, D, H, W) -> (C, N * D * H * W)
    return transposed.contiguous().view(C, -1)

def per_channel_dice_loss(x, y, **kwargs):
    return 1 - compute_per_channel_dice(x, y, **kwargs).mean()

def weighted_loss(input, target, weights, loss_func, weighted_dimension=1):
    losses = torch.zeros(input.shape[weighted_dimension])
    for index in range(input.shape[weighted_dimension]):
        x = input.select(dim=weighted_dimension, index=index)
        y = target.select(dim=weighted_dimension, index=index)
        losses[index] = loss_func(x, y)
    return torch.mean(weights * losses)

class WeightedLoss(object):
    def __init__(self, weights, loss_func, weighted_dimension=1):
        self.weights = weights
        self.loss_func = loss_func
        self.weighted_dimension = weighted_dimension

    def __call__(self, input, target):
        return weighted_loss(input=input, target=target, weights=self.weights, loss_func=self.loss_func,
                             weighted_dimension=self.weighted_dimension)
