--- 
title: Teacher forcing & scheduled sampling  
date: 2022-10-16 12:22.214030
draft: false
summary: "A short documentation on teacher forcing to training recurrent neural networks. Additional a scheduled sampling module to control teacher forcing prcoess during training."
weight: -9
tags:
  - machine learning
  - deep learning
  - teacher forcing
  - rnn 
cover: 
  image: "scheduled_sampler_plots.png"
---
  
During recent projects I came across two concepts teacher forcing and scheduled sampling.
Teacher forcing is a technique to train recurrent neural networks (rnns). Where as scheduled
sampling is more a general probability sampling method, which could be used in more 
scenarios. 

# Teacher forcing

In complex challenges like for example sound event detection (SED) there might be multiple
training objectives. SED comes with two objectives:
1. predict classes
2. predict event boundaries

To meet both objectives with one network one could train a CRNN (convolutional recurrent
network). The problem when training the RNN on top of the CNN is a very general problem: 
Since the recurrency works by passing the previous states, predicting the early state falsly
propagates the error through the time steps and slows down training.

> Teacher forcing leak `targets` during training at randomly chosen time steps with some 
> probability to hint the model towards the correct learning path.

This seams like cheating, and exploits the training prcoess to potential overfitting, so one has 
to choose the probability wisely or the model will dramatically overfit. 

# Example model

As a basis for this process I rely on the illustrations and strategy chosen by K. Drossos et.al.:
[Language modelling for sound event detection with teacher forcing and scheduled sampling](https://arxiv.org/abs/1907.08506).
Their publication uses a CRNN (a RNN head with CNN blocks as a basis), to train 
spectogram sequences of the DCase Tasks of 2016 and 2017. 

First we need some features. Here I'd like to recommend [`torchlibrosa`](https://github.com/qiuqiangkong/torchlibrosa).
Be aware both `Spectrogram` and `LogmelFilterBank` are coming from `torchlibrosa`.
We do the same as Drossos et.al.:

````Python
{! ./python_examples/teacher_forcing_scheduled_sampler/example_001.py [ln:8-] !}
````

Note we generated some random class targets with a shape of `(1, 107, 6)`, where 1 is the 
batch_size, 107 is the number of timesteps and 6 our number of classes. Up next we need a
model with an RNN head, we'll also use the proposed one of Drossos et.al.:

````Python
{! ./python_examples/teacher_forcing_scheduled_sampler/example_002.py [ln:22-79] !}
````

They use three convolution blocks that differ in the `kernel_size` and `stride` of the 
max pooling layer. On top of that they use a `GRUCell` as the recurrency network and a
single fully connected layer accepting the output of the RNN and outputting the number
of classes. The last layer is also known as feed-forward neural network (FNN/FFN).
Their design focuses on the design of the gradient recurrent unit (`GRUCell`), which 
has a slightly different input (`conv_dims + num_classes`). Like this they can first input
the to the `feature_module` and the `convolutions`, to then concat this output with the
RNNs output and randomly force the `forward`-step to concat the `convolutions` with 
the correct `targets` of a timestep `t`. If they randomly select not to leak the `targets` 
of `t`-th timestep they select the output of the former classification step as input for
the RNN. The process looks like this:

````Python
{! ./python_examples/teacher_forcing_scheduled_sampler/example_002.py [ln:81-116] !}
````

The important in the above `forward`-step is the decision wether or not to use the correct
`targets`, which is performed at every timestep `t`:

````Python
{! ./python_examples/teacher_forcing_scheduled_sampler/example_002.py [ln:109-113] !}
````

Not that we keep all the original `out` variables in `outputs`, so the loss is later
correctly calculated (`outputs[:, t, :] = out`).

# Scheduled sampling

> Scheduled sampling (in this case) is a method to sample probabilities for the controlled 
> use of teacher forcing. This concept aims to guide the training during the crucial first 
> iterations.

Teacher forcing will only thrive in sequence prediction if combined with a good sampling
strategy. Scheduled sampling was proposed by S. Bengio et.al. in 
[Scheduled Sampling for Sequence Prediction with Recurrent Neural Networks](https://arxiv.org/abs/1506.03099v1).
They propose their strategy for different sequence prediction applications, like 
Image Captioning, Constituency Parsing and Speech Recognition. Their strategy consists of
a decreasing function which can have different properties e.g. linear, sigmoid or
exponential. 

The strategy by Drossos et.al. is linked to the number of batches, to control the decrease 
of teacher-forcing probability with iterations the model was trained on. They discribe it
as:

$$ p_{tf} = min(p_{max}, 1 - min(1 − p_{min}, \frac{2}{1 + e^{\beta}} - 1)),\ where\ \beta = -\gamma \frac{i}{N_{b}} $$

This is an expoential decrease, where \\( e^{ \beta } \\) is the decreasing factor, because *i* 
is rising with each iteration a new probability is sampled and N is the number of batches
in a single epoch and \\( \gamma \\) controlls the slope.

This way the training process can sample a new probability everytime a new batch arrives 
or during the sequential prediction for every timestep. To visualize the samples we can use 
the slope that will be influenced by \\( \gamma \\) here's a small illustration of how it's 
build:

````Python
{! ./python_examples/teacher_forcing_scheduled_sampler/example_003.py [ln:9-33] !}
````

The following example assumes a few parameters, initilizes a sampler for each configuration
and runs `N * T` weight updates to generate some probabilities. Just for clarification 
`T` is the parameter for the time steps in the `inputs`/`target` data shape, which is 
also the number of times the RNN predicts per sample.

````Python
{! ./python_examples/teacher_forcing_scheduled_sampler/example_003.py [ln:36-62] !}
````

The result shows the higher `gamma` the faster `p_min` is hit. Also it shows well how the 
first iterations are capped by the `p_max` parameter. The number of batches `N` (in the 
training dataset) together with the models/samplers current `iteration` together with 
`gamma` controlls the decrease, such that the model does not overfit fast, but the rnn
training is still guided efficiently.

{{< figure src="/scheduled_sampler_plots.png#center" class="quarter-sized" caption="Sampling strategy by Bengio et.al. with different configurations. Slope of sampled probabilities is controlled by the gamma." >}}

# Both together

If we plug this sampler into the model we can generate a *new* probability each time,
either when a new batch arrives or when the rnn predicts a new time step. The latter
scenario is the case for teacher-forcing. Just adapt the `__init__` of `CRNN` to 
recieve `tf_prob_sampler: ScheduledSampler` and add it to the module, so the scheduler
can be used with `self.tf_prob_sampler`. The rest is done in `get_forced_targets`.

````Python
{! ./python_examples/teacher_forcing_scheduled_sampler/example_004.py [ln:26-40] !}
{! ./python_examples/teacher_forcing_scheduled_sampler/example_004.py [ln:57] !}
        # ...

{! ./python_examples/teacher_forcing_scheduled_sampler/example_004.py [ln:61-68] !}
````

In the following I generated sample teacher-forcing draws to simulate what it would feel
like when training a model. We return both the `targets_forced` plus `sampled_probs` from
the `forward` call and plot while training epochs rise and so do the `sampler`s 
`iteration` values.

Here is a simulation with 
* 50 batches
* batch_size 16
* each sample with 107 time steps

{{< figure src="/scheduled_sampling.gif" caption="The above schedule with `gamma=0.08` (bottom), together with the forced samples per batch and timestamp on the bottom. Blue tiles are teacher forced `targets` and replaced in the batch and timestamp for the RNNs prediction in `t+1`. White tiles are rnn predictions." >}}

In the beginning there is clear a lot of blue tiles (true `targets`) are passed to the rnn
inputs, meaning the rnns original prediction is replaced with true `targets` in these
time steps, whereas the white ones are original prediction. As the iterations rise, these
drop drastically in frequency until `p_min` is hit. Like this scheduled sampling as a 
guiding effect to the rnns training, without overfitting instantly.

> PS: If you want to replicate the experiment: All sources are available at
> [github.com/arrrrrmin/arrrrrmin.netlify.com](https://github.com/arrrrrmin/arrrrrmin.netlify.com/tree/main/code/python-examples/python_examples/teacher_forcing_scheduled_sampler)
> Enjoy 🎉
