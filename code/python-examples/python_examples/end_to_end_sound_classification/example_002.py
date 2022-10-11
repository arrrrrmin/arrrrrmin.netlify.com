from collections import OrderedDict
from typing import Union

from torch import Tensor
from torch.nn import (
    Module,
    Sequential,
    Linear,
    ReLU,
    Dropout,
    MaxPool2d,
    Flatten,
    Conv2d,
    BatchNorm2d,
)


class ConvBlock(Module):
    def __init__(
        self, in_channels: int, out_channels: int, kernel_size: Union[int, tuple]
    ):
        super(ConvBlock, self).__init__()
        self.module = Sequential(
            Conv2d(in_channels, out_channels, kernel_size, bias=False),
            BatchNorm2d(out_channels),
            ReLU(),
        )

    def forward(self, X: Tensor) -> Tensor:
        return self.module(X)


class Transpose(Module):
    def __init__(self, target: int, destination: int):
        super(Transpose, self).__init__()
        self.target = target
        self.destination = destination

    def forward(self, X: Tensor) -> Tensor:
        return X.transpose(self.target, self.destination)


class LinearBlock(Module):
    def __init__(self, in_features: int, out_features: int):
        super(LinearBlock, self).__init__()
        self.module = Sequential(
            Linear(in_features, out_features),
            ReLU(),
            Dropout(),
        )

    def forward(self, X: Tensor) -> Tensor:
        return self.module(X)


class EnvNet(Module):
    def __init__(self, num_classes: int):
        super(EnvNet, self).__init__()
        self.num_classes = num_classes
        self.feature_conv = Sequential(
            OrderedDict(
                [
                    ("conv1", ConvBlock(1, 40, (1, 8))),
                    ("conv2", ConvBlock(40, 40, (1, 8))),
                    ("pool2", MaxPool2d((1, 160))),
                    ("transpose", Transpose(1, 2)),
                ]
            )
        )
        self.classifier = Sequential(
            OrderedDict(
                [
                    ("conv3", ConvBlock(1, 50, (8, 13))),
                    ("pool3", MaxPool2d(3)),
                    ("conv4", ConvBlock(50, 50, (1, 5))),
                    ("pool4", MaxPool2d((1, 3))),
                    ("flatten", Flatten(1, -1)),
                    ("fc5", LinearBlock(50 * 11 * 14, 4096)),
                    ("fc6", LinearBlock(4096, 4096)),
                    ("fc7", Linear(4096, self.num_classes)),
                ]
            )
        )


import torch

model = EnvNet(num_classes=50)
x = torch.rand(1, )
print()
