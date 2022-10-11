import numpy as np
import torch
from torch.nn import Sequential, MaxPool2d

from example_002 import ConvBlock, Transpose


def overlapping_samples_post_conv(num_sample: int, filter_size: int) -> int:
    return num_sample // (num_sample // filter_size) - 1


# Batch size N, audio channels, sample rate, number of classes, seconds per sample
N, channels, S, C, sec_per_sample = (1, 1, 16000, 50, 1.5)
# Find the number of samples to additionally take from the sample, so the convolution
# strides to even length (multiply by 2 since we have the same stride two times).
pad_samples = overlapping_samples_post_conv(S, 8) * 2
sample_size = int(np.floor(S * sec_per_sample + pad_samples))
# Simulated sound with the configured sample size
inputs = torch.rand(N, channels, sample_size)
# Unsqueeze so it fits into Conv2d
inputs = inputs.unsqueeze(1)

feature_conv = Sequential(
    ConvBlock(1, 40, (1, 8)),
    ConvBlock(40, 40, (1, 8)),
    MaxPool2d((1, 160)),
    Transpose(1, 2),
)

for module in feature_conv:
    print(module.__class__.__name__)
    inputs = module(inputs)
    print(inputs.size())

# ConvBlock
# torch.Size([1, 40, 1, 24007])
# ConvBlock
# torch.Size([1, 40, 1, 24000])
# MaxPool2d
# torch.Size([1, 40, 1, 150])
# Transpose
# torch.Size([1, 1, 40, 150])
