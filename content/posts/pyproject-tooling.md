---
title: Pyproject Tooling
date: 2021-10-16 12:22.214030
draft: false
summary: "Tooling for a conviniently lightweight python project, using pyproject.toml with some simple tools"
weight: -4
---

In recent projects I wanted to go a bit deeper into how properly set up a python project.
There are many nice packages and tools to support development, testing, packaging and
releasing these packages. So this is a small brain dump regarding tools and packages that
make development live a bit more convinient.

# Poetry

For dependency management, packaging and many other convinient features 
[poetry](https://python-poetry.org) is a good way to start. First install poetry:

````bash
# https://python-poetry.org/docs/#installation
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
which poetry
````

Init a new project:
````bash
poetry new myproject
````
Poetry does multiple things here. First it creates a package structure for the project,
second it creates a virtual environment. If you want to see where this env is located, run
`poetry run which python`. This is the path you usually want to pass to your IDE as the 
project's python interpreter. It also creates a `pyproject.toml`, which is the central 
place your project config lives in.

Install a dependency
````bash
# Add pydantic to projects core dependencies 
poetry add pydantic
# Install with package extras
poetry add pydantic -E dotenv
# Install from git (useful for private repos)
# poetry add git+ssh://git@github.com:<org>/<repo>.git#<rev>
poetry add git+ssh://git@github.com:samuelcolvin/pydantic.git#4be3f45
# Add development dependency
poetry add -D black flake8 flake8-unused-arguments pytest
````

## pyproject.toml

These commands will result in a `pyproject.toml` update which will look somewhat like:

````toml
[tool.poetry]
name = "myproject"  # project name
version = "0.1.0"
description = "Description for myproject package"
authors = ["arrrrrmin <arrrrrrmin@no-reply>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.9"
pydantic = "^1.8.2"

[tool.poetry.dev-dependencies]
pytest = "^5.2"
black = "^21.9b0"
poethepoet = "^0.10.0"
flake8 = "^4.0.1"
flake8-unused-arguments = "^0.0.6"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
````

If you now want to access the env poetry created, simply do `poetry shell`. It's the same
as `source env/bin/activate`, when working with `venv`. 

## poe the poet

Our `pyproject.toml` is also a nice place to have tooling config in. I personally like
[poe the poet](https://pypi.org/project/poethepoet/). I found this to be one of the 
easiest ways to define tasks in the toml file. One can also use separate bash scripts for
more complexe things, if needed.  Here is an example:

````toml
# Pyproject.toml
# ...

[tool.poe.tasks]
format = "black myproject/"
lint = [
  { cmd = "black myproject/ --check --diff --verbose" },
  { cmd = "flake8 myproject/" },
]
test = "pytest ./ -vv"
coverage = "pytest --cov=./myproject --cov-report=xml --verbose"
clean-up = "rm -rf .pytest_cache dist/ ./**/__pycache__ .coverage"
````

The example defines 5 tasks: `format`, `lint`, `test`, `coverage` and `clean-up`. Runnning
one of these is pretty simple: `poetry run poe <cmd>`. Most of the time there is also some
more configuration for the tools, wrapped in these commands. One example could be black.
Run it like this


I perfer to have a line-length of 90 characters, either we have to create a `cfg` or some 
other config file. Since we have a `pyproject.toml` already let's just pass configuration 
here:

````toml
# Pyproject.toml
# ...

[tool.black]
line-length = 90
````

So, if you now run `poetry run poe format` `black` will take `line-length = 90` as 
configration, since `[tool.black]` hints it. This also works for all python tools, that
support `pyproject.toml` as a possible configuration way. Mostly I work with:
* `poetry`
* `poe`
* `pytest`
* `black`
* `falke8`

I trigger my commonly used actions with poe, which will also be used in github actions. 

````bash
# From outside of the environment
poetry run poe lint
poetry run poe format
poetry run poe test
poetry run poe coverage
poetry run poe clean-up
# If you chose to work inside the environment you can skip 'poetry run'
````
