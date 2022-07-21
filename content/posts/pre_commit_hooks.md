---
title: Pre-Commit hooks
date: 2022-072-20 17:04.214030
draft: false
summary: "An introduction to pre-commit and how to build custom python hooks for pre-commit."
weight: -7
tags:
  - pre-commit
  - python
  - hooks
  - git
cover:
  image: "pre_commit_hooks.png"
---

> A framework for managing and maintaining multi-language pre-commit hooks.

A few weeks ago I came across [`pre-commit`](https://github.com/pre-commit/pre-commit). 
It's a pretty useful framework, to generate pre-commit hooks that are used to check code, before
committing it to your branch. It's pretty popular in the python community, but also provides
it's functionality for multiple languages. For more see the list of 
[supported languages](https://pre-commit.com/#supported-languages). 

## Hooks
Without any hooks pre-commit doesn't make a lot of sense, so let's see what these hooks do. 
Hooks are small programms that check your committed changes and raise an error (status code 1) if
your commits do not pass the hooks check. Basically pre-commit holds the foot into the door, 
if you'r committed changes not following the spec put up by your hooks config. So it prevents you
from committing code with *low quality*. 
The diagram below illustrates this behaviour:

![Pre-Commit-Hooks Process](/pre_commit_hooks.png)

## Get started

- Install with `brew install pre-commit` or `pip install pre-commit`
- Go to the top of your repo
- Create a config file with `touch .pre-commit-config.yaml`
- Fill your config with a sample file `pre-commit sample-config > .pre-commit-config.yaml`
- Install pre-commit-hooks in your repo `pre-commit install`

With `pre-commit sample-config > .pre-commit-config.yaml` we filled our config file with pre-commits 
default content. The `.pre-commit-config.yaml` now contains the following

````yaml
# See https://pre-commit.com for more information
# See https://pre-commit.com/hooks.html for more hooks
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v3.2.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
````

It says take `hooks` from `repo` with `id: trailing-whitespace`. So `pre-commit/pre-commit-hooks` 
provides multiple useful hooks, you can simply plug in. See the list of officially supported hooks 
[here](https://pre-commit.com/hooks).

## Other hooks

One example for other hooks/executable programms could be `black` (a python formatter). The repo your
adding has to have a `.pre-commit-hooks.yaml` file. This file tells pre-commit where the executable (`entry`)
is, what language is uses (`language`) or for example what files it's running on `files` 
(the latter is a pattern). Most important it tells what `id` to use in the config file.
You can add it and it'll be executed on commit (or the stage you want to to be execeuted, more about this later). 
Add `black` like this:

````yaml
repos:
-   repo: https://github.com/psf/black
    rev: 22.6.0
    hooks:
    -   id: black
````

Please have in mind the `rev` value does not automatically updates if you run 
`pre-commit autoupdate` For more about this see 
[blacks-documentation](https://black.readthedocs.io/en/stable/integrations/source_version_control.html?highlight=pre-commit#version-control-integration).
Further external hooks will also define a `.pre-commit-config.yaml` file. It'll tell your config file which
defaults to use for configuration.

## Configure hooks

The above example, just tells pre-commit to take a set of hook ids from a repo. In case of black, you'd configure 
the formatter using `[[tool.black]]` in a `pyproject.toml`, but there's a more to configure, on the pre-commit side.
As mentioned in [other hooks](#other-hooks), defaults are coming from the source repos `.pre-commit-config.yaml` file.
You can overwrite these in your `.pre-commit-config.yaml`. See the list of possible arguments at pre-commits 
[documentation](https://pre-commit.com/#pre-commit-configyaml---hooks).

A good example is `stages` or `always_run`. `always_run` is pretty self-explainatory. `stages` can configure
when the hook is running. Possible values: `commit`, `merge-commit`, `push`, `prepare-commit-msg`, `commit-msg`, `post-checkout`, 
`post-commit`, `post-merge`, `post-rewrite`, or `manual`. If you install the hooks with `-t` or `--hook-type` you also can
tell the hook when it should run. Default is `all-stages`. To install all your hooks to run on push would be 
`pre-commit install --hook-type push`.

If you want to see how a hook works, you can execute a single hook with `pre-commit run <hook-id>`. In case you
develop your own hook [`pre-commit try-repo`](https://pre-commit.com/#pre-commit-try-repo) is a nice solution to test
a hooks behaviour. For your own custom hook development have a look at: 
* [creating new hooks](https://pre-commit.com/#creating-new-hooks)
* [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks)
