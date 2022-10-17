import torch
import torchaudio
from torch import nn, Tensor
from torchaudio.utils import download_asset
from torchlibrosa import Spectrogram, LogmelFilterBank


class FeatureExtractor(nn.Module):
    def __init__(
        self,
        window_len: int,
        hop_len: int,
        sample_rate: int,
        n_mels: int,
        n_fft: int,
        is_log: bool,
    ):
        super(FeatureExtractor, self).__init__()
        self.module = nn.Sequential(
            Spectrogram(n_fft, hop_len, window_len),
            LogmelFilterBank(sample_rate, n_fft, n_mels, is_log=is_log),
        )

    def forward(self, inputs: Tensor) -> Tensor:
        return self.module(inputs)


if __name__ == "__main__":
    sample_wav = download_asset(
        "tutorial-assets/Lab41-SRI-VOiCES-src-sp0307-ch127535-sg0042.wav"
    )
    waveform, sr = torchaudio.load(sample_wav)
    print(waveform.size(), sr)
    # torch.Size([1, 54400]) 16000
    feature_module = FeatureExtractor(1024, 512, sr, 40, 2048, False)
    print(feature_module(waveform).size())
    # torch.Size([1, 1, 107, 40])
    y = torch.randint(low=0, high=2, size=(107, 6)).unsqueeze(0)
    print(y.size())
    # torch.Size([1, 107, 6])
