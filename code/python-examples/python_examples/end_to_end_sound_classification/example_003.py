import torch
from torch.nn import Conv2d

# A convolution of 1 input dims and 32 output dims, with
# padding of 1 in both dimensions and a stride of 2 in both
# dimensions of the convolution.
c = Conv2d(1, 32, 3, padding=(1, 1), stride=(2, 2))
x = torch.rand(4, 1, 5, 5)
print(c(x).shape)
# torch.Size([4, 32, 3, 3])
print(c.weight.size())
# torch.Size([32, 1, 3, 3])
