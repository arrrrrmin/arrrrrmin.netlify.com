from typing import Tuple

import numpy as np
import torch
from torch import nn, Tensor
import matplotlib.pyplot as plt


class ScheduledSampler(nn.Module):
    def __init__(
        self,
        num_batches: int,
        gamma: float,
        p_min: float = 0.05,
        p_max: float = 0.95,
    ):
        super(ScheduledSampler, self).__init__()
        self.N = num_batches
        self.gamma = gamma
        self.p_min = p_min
        self.p_max = p_max
        self.iteration = 0

    @property
    def exp_beta(self) -> float:
        return Tensor([-self.gamma * (self.iteration / self.N)]).exp().item()

    def forward(self, batch_size: int) -> Tuple[Tensor, float]:
        p = min(self.p_max, 1 - min(1 - self.p_min, (2 / (1 + self.exp_beta)) - 1))
        return torch.rand(batch_size).lt_(p), p

    def update_iteration(self) -> None:
        self.iteration += 1


if __name__ == "__main__":
    N = 50
    B = 16
    T = 107
    sampler_config = [
        {"gamma": 0.01, "p_min": 0.05, "p_max": 0.95},
        {"gamma": 0.02, "p_min": 0.05, "p_max": 0.9},
        {"gamma": 0.08, "p_min": 0.025, "p_max": 0.8},
        {"gamma": 0.10, "p_min": 0.01, "p_max": 0.7},
    ]
    samplers = [ScheduledSampler(N, **conf) for conf in sampler_config]
    sampled_probs = [[], [], [], []]
    for _ in range(N * T):
        for idx, sampler in enumerate(samplers):
            sampled_probs[idx].append(sampler(B)[1])
            sampler.update_iteration()
    for idx in range(len(samplers)):
        label = ", ".join([f"{k}:{v}" for k, v in sampler_config[idx].items()])
        plt.plot(np.arange(len(sampled_probs[idx])), sampled_probs[idx], label=label)
    plt.legend()
    plt.xlabel("Iteration")
    plt.ylabel("Probabiliy")
    plt.tight_layout()
    plt.savefig("scheduled_sampler_plots.png")
    plt.show()
