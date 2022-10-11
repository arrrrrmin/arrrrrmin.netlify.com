from collections import OrderedDict

import torchaudio
from torch import nn

from torchaudio.utils import download_asset


sample = download_asset(
    "tutorial-assets/Lab41-SRI-VOiCES-src-sp0307-ch127535-sg0042.wav"
)
signal, sample_rate = torchaudio.load(sample)
print(signal.size())
# torch.Size([1, 54400])
print(signal.min(), signal.max())
# tensor(-1.0000) tensor(0.6682)
print(signal.nonzero().min(), signal.nonzero().max())
# tensor(0) tensor(54399)
