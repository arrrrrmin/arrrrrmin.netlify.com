from matplotlib import pyplot as plt
from torch import Tensor
from torch.nn import (
    Module,
    Dropout,
    Sequential,
    GRUCell,
    Linear,
)
from typing import Optional, Dict, Tuple

import torch
import numpy as np

from python_examples.teacher_forcing_scheduled_sampler.example_001 import FeatureExtractor
from python_examples.teacher_forcing_scheduled_sampler.example_002 import ConvolutionBlock
from python_examples.teacher_forcing_scheduled_sampler.example_003 import ScheduledSampler


def init_dropout(module: Module, p: float):
    for mod in module.modules():
        if isinstance(mod, Dropout):
            mod.p = p


class CRNN(Module):
    def __init__(
        self,
        conv_dims: int,
        rnn_hidden_dims: int,
        num_classes: int,
        dropout: float,
        tf_prob_sampler: ScheduledSampler,  # Provide the module
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
        self.tf_prob_sampler = tf_prob_sampler
        self.num_classes = num_classes
        init_dropout(self, dropout)

    def get_forced_targets(
        self, batch_size: int, is_inference: bool
    ) -> Tuple[Tensor, float]:
        if is_inference:
            return torch.zeros(batch_size), 0.0
        force_targets, p = self.tf_prob_sampler(batch_size)
        self.tf_prob_sampler.update_iteration()
        return force_targets, p

    def forward(
        self, inputs: Tensor, targets: Optional[Tensor] = None
    ) -> Dict[str, Tensor]:
        features = self.feature_module(inputs)
        B, _, T, M = features.size()
        C = self.num_classes

        features = self.convolutions(features).permute(0, 2, 1, 3)
        features = features.squeeze(-1)

        teacher_force = torch.zeros(B, C)

        h = torch.zeros(B, self.rnn.hidden_size)
        outputs = torch.zeros(B, T, self.num_classes)

        targets_forced = []
        sampled_probs = []
        for t in range(T):
            rnn_features = torch.cat([features[:, t, :], teacher_force], dim=-1)

            h = self.rnn(rnn_features, h)
            out = self.fnn(h)
            rnn_inputs = out.sigmoid().gt(0.5).float()

            # We call a new probability each time step (T)
            force_targets, prob = self.get_forced_targets(B, (targets is None))
            sampled_probs.append(prob)
            targets_forced.append(force_targets)
            for batch_idx, force in enumerate(force_targets):
                teacher_force[batch_idx, :] = (
                    targets[batch_idx, t, :] if force else rnn_inputs[batch_idx, :]
                )
            outputs[:, t, :] = out
        targets_forced = torch.stack(targets_forced, dim=0)
        return {
            "outputs": outputs,
            "targets_forced": targets_forced,
            "sampled_probs": sampled_probs,
        }


import matplotlib as mpl

if __name__ == "__main__":
    N = 50  # number of batches
    B = 16  # batch size
    T = 107  # time steps
    batch_tensor = torch.rand(16, 54400)
    y = torch.randint(low=0, high=2, size=(B, 107, 6))
    sampler = ScheduledSampler(N, gamma=0.08, p_min=0.05, p_max=0.9)
    model = CRNN(128, 128, 6, 0.2, sampler)
    targets_forced = []
    sampled_probs = []
    for _ in range(N):
        model_outputs = model(batch_tensor, y)
        targets_forced.append(model_outputs["targets_forced"])
        sampled_probs.append(model_outputs["sampled_probs"])
    targets_forced = torch.stack(targets_forced).permute(0, 2, 1)
    sampled_probs = torch.flatten(torch.tensor(sampled_probs))
    for batch_idx in range(N):
        fig, ax = plt.subplots(2, figsize=(8, 5))
        fig.suptitle(f"Probabilities and forced targets at batch {batch_idx}")
        ax[0].imshow(targets_forced[batch_idx, :, :], cmap=mpl.colormaps["Blues"])
        ax[0].set_xlabel("Time step")
        ax[0].set_ylabel("Batch")
        ax[1].plot(
            np.arange(len(sampled_probs[: int(batch_idx * T)])),
            sampled_probs[: int(batch_idx * T)],
            label="Sampled probs",
        )
        ax[1].set_xlabel("Iteration")
        ax[1].set_ylabel("Prob")
        plt.savefig(f"SampledProbs/tf_batch_{batch_idx}.jpg")
