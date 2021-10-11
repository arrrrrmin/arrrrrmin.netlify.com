---
title: Pydantic powers
date: 2021-08-21 12:22.214030
draft: false
summary: "Some awesome tips and tricks one can do with pydantic. Data validation with pydantic and never load json without pydantic anymore. Example usage with boto3 (aws sdk for python)."
weight: -2
---

This is my personal though and development bubble, so let's talk 
[Pydantic](https://github.com/samuelcolvin/pydantic)! 
Since I first used [FastAPI](https://github.com/tiangolo/fastapi) I'm a huge fan of 
[Pydantic](https://github.com/samuelcolvin/pydantic). Basically it's about data 
validation. As a developer it's often about recieving data from somewhere, doing something
with it and passing it on to somewhere else. When recieving data, I like to know if it 
follows the structure I expect. When sending stuff elsewhere, I'd like to make sure 
everything is following some other structure. 

> TL;DR: pydantic models are a lot of fun! 

# Basics

First of the following examples might include one or more of the folloing imports:

```Python
from datetime import datetime
from typing import Union, Optional, List, Dict, Literal
from uuid import UUID
from pydantic import BaseModel
```

Pydantic models work pretty straight forward.

- Define a model with standard python type hinting (define data shape)
- Load data in a model
- Validate data passed to the model (this is done by pydantic) 
- Enjoy your easily implemented data shape 🎉

A simple model could look like this:

````Python
{! ./python_examples/pydantic_powers/example_001.py [ln:1-8] !}
````

So far so good, We created a python class inheriting from BaseModel, which gives us 
pydantics validator powers. Such that whenever data doesn't pass our models spec, 
pydantic will raise proper errors for us. It'll look like so:

````Python
{! ./python_examples/pydantic_powers/example_001.py [ln:10-26] !}
````

Like with every other class we can define function for this one too. This comes especially
handy with larger classe, that have mutple sub models, but this is a later topic. Here is 
a class function that works with our `text` variable:

````Python
{! ./python_examples/pydantic_powers/example_002.py !}
````

# More typing

One can also work with import from `typing`. I personally often use the following:

- `Union`: On of the passed types must be fulfilled
- `Optional`: Not required
- `List`: is a list of passed types
- `Dict`: is a dictionary
- `Literal`: One of the following strings is allowed

In case of `Dict` one can also build a new pydantic model and pass it as a type to the 
parent model. Like this it's possible to validate children as well since `**` would be 
implicit in these cases.

```Python
{! ./python_examples/pydantic_powers/example_003.py [ln:1-15] !}
```

You can run this code as is, which can be used like so:

```Python
{! ./python_examples/pydantic_powers/example_003.py [ln:18-30] !}
```

# Custom validation

In case we have some non-standard data type we can also use custom data validation. 
For example, we could `from pydantic import HttpUrl`. This allows us to parse and validate
something like `https://arrrrrmin.netlify.com/`. If we'd have a response from some 
aws service recieved by FastAPI, we should be able to validate something like 
`s3://bucket/folder/file.json`, which fails with `HttpUrl`. The following validator can 
handle this:

```Python
{! ./python_examples/pydantic_powers/example_004.py [ln:1-62] !}
```

You can run this code as is, which can be used like so:

```Python
{! ./python_examples/pydantic_powers/example_004.py [ln:63-] !}
```

Ok, let's break it down a bit. First we declared what we need and took advantage of 
`typing.Optional`.

```Python
{! ./python_examples/pydantic_powers/example_004.py [ln:25-31] !}
```

Our parameters `bucket`, `path` and `key` are optional at first, but will be filled when 
their values become available in `root_validator`, which is the first validator executed, 
by pydantic. With `validate_root_uri` we inspect all `values` recieved by `S3Uri`. We
break it into pieces and fill our optional parameters. By nature an S3Uri needs a bucket, 
which we'll enforce here:

```Python
{! ./python_examples/pydantic_powers/example_004.py [ln:39-42] !}
```

Everything else below is just to see wether or not our parsed vales fullfill what we 
expect, such that these are prompted like pydantic intends to.

# Aliases

In some cases, for example working with FastAPI it's useful to work with aliases. Aliases
will help to have [PEP8](https://www.python.org/dev/peps/pep-0008/) (snake-case) 
compatible names, by also support camel-case naming, when creating the model. Here is an
example: 

```Python
{! ./python_examples/pydantic_powers/example_005.py !}
```

Like this it's possible to use snake- and camel-case naming when passing data. There is a 
lot more to explore at [Pydantic documentation](https://pydantic-docs.helpmanual.io).
