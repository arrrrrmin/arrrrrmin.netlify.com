import torchaudio
from torch import Tensor
from torch.nn import (
    Module,
    Dropout,
    Sequential,
    Conv2d,
    BatchNorm2d,
    ReLU,
    MaxPool2d,
    GRUCell,
    Linear,
)
from typing import Union, Tuple, Optional

import torch
from torchaudio.utils import download_asset

from python_examples.teacher_forcing_scheduled_sampler.example_001 import FeatureExtractor


def init_dropout(module: Module, p: float):
    for mod in module.modules():
        if isinstance(mod, Dropout):
            mod.p = p


class ConvolutionBlock(Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        maxpool_kernel_size: Union[int, Tuple[int, int]],
        maxpool_stride: Union[int, Tuple[int, int]],
    ):
        super(ConvolutionBlock, self).__init__()
        self.module = Sequential(
            Conv2d(in_channels, out_channels, kernel_size=5, stride=1, padding=2),
            BatchNorm2d(out_channels),
            ReLU(),
            MaxPool2d(kernel_size=maxpool_kernel_size, stride=maxpool_stride),
        )

    def forward(self, inputs: Tensor) -> Tensor:
        return self.module(inputs)


class CRNN(Module):
    def __init__(
        self,
        conv_dims: int,
        rnn_hidden_dims: int,
        num_classes: int,
        dropout: float,
        window_len: int = 1024,
        hop_len: int = 512,
        sample_rate: int = 16000,
        n_mels: int = 40,
        n_fft: int = 2048,
        is_log: bool = False,
    ):
        super(CRNN, self).__init__()
        self.feature_module = FeatureExtractor(
            window_len=window_len,
            hop_len=hop_len,
            sample_rate=sample_rate,
            n_mels=n_mels,
            n_fft=n_fft,
            is_log=is_log,
        )
        self.convolutions = Sequential(
            ConvolutionBlock(1, conv_dims, (1, 5), (1, 5)),
            ConvolutionBlock(conv_dims, conv_dims, (1, 4), (1, 4)),
            ConvolutionBlock(conv_dims, conv_dims, (1, 2), (1, 2)),
        )
        self.rnn = GRUCell(conv_dims + num_classes, rnn_hidden_dims, bias=True)
        self.fnn = Linear(rnn_hidden_dims, num_classes, bias=True)
        self.num_classes = num_classes
        init_dropout(self, dropout)

    @property
    def teacher_forcing_prob(self) -> float:
        return 0.7  # This will change when using scheduled sampling!

    def get_forced_targets(self, batch_size: int, is_inference: bool) -> Tensor:
        if is_inference:
            return torch.zeros(batch_size)
        return torch.rand(batch_size).lt_(self.teacher_forcing_prob)

    def forward(self, inputs: Tensor, targets: Optional[Tensor] = None) -> Tensor:
        features = self.feature_module(inputs)
        B, _, T, M = features.size()
        C = self.num_classes

        features = features.transpose(2, 3)
        features = self.convolutions(features).permute(0, 2, 1, 3).contiguous()
        features = features.squeeze(-1)

        teacher_force = torch.zeros(B, C)

        h = torch.zeros(B, self.rnn.hidden_size)
        outputs = torch.zeros(B, T, self.num_classes)

        for t in range(T):
            features = torch.cat([features[:, t, :], teacher_force], dim=-1)

            h = self.rnn(features[:, t, :], h)
            out = self.fnn(h)
            rnn_inputs = out.sigmoid().gt(.5).float()

            force_targets = self.get_forced_targets(B, (targets is None))
            for batch_idx, force in enumerate(force_targets):
                teacher_force[batch_idx, :] = (
                    targets[batch_idx, t, :] if force else rnn_inputs[batch_idx, :]
                )
            outputs[:, t, :] = out
        return outputs


if __name__ == "__main__":
    sample_wav = download_asset(
        "tutorial-assets/Lab41-SRI-VOiCES-src-sp0307-ch127535-sg0042.wav"
    )
    waveform, sr = torchaudio.load(sample_wav)
    print(waveform.size(), sr)
    # torch.Size([1, 54400]) 16000
    y = torch.randint(low=0, high=2, size=(107, 6)).unsqueeze(0)
    print(y.size())
    # torch.Size([1, 107, 6])

    model = CRNN(128, 128, 6, 0.2)
    print(model.feature_module(waveform).size())
    # torch.Size([1, 1, 107, 40])
