---
title: Pydantic powers
date: 2021-08-21 12:22.214030
draft: false
summary: "Some awesome tips and tricks one can do with pydantic. Data validation with pydantic and never load json without pydantic anymore. Example usage with boto3 (aws sdk for python)."
weight: -2
tags:
  - python types
  - validation
  - data shapes
  - pydantic
---

This is my personal thought and development bubble, so let's look at
[Pydantic](https://github.com/samuelcolvin/pydantic)! 
Since I first used [FastAPI](https://github.com/tiangolo/fastapi) I'm a huge fan of 
[Pydantic](https://github.com/samuelcolvin/pydantic). Basically it's about data 
validation. As a developer it's often about recieving data from somewhere, doing something
with it and passing it on to somewhere else. When recieving data, I like to know if it 
follows the structure I expect. When sending stuff elsewhere, I'd like to make sure 
everything is following a structure. So pydantic was a handy way to ensure these i/o
patterns.

> TL;DR: pydantic models enable handy, standardized data wrapping and validation!

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
import uuid
from pydantic import BaseModel


class RawSentence(BaseModel):
    id: uuid.UUID  # An id has to match a UUID
    text: str  # The text has to match a normal str

````

So far so good, We created a python class inheriting from BaseModel, which gives us 
pydantics validator powers. Such that whenever data doesn't pass our models spec, 
pydantic will raise proper errors for us. It'll look like so:

````Python
if __name__ == "__main__":
    data_point = {
        "id": "4a3f61a9-8e75-4341-b3a0-3e64e0b60fb6",
        "text": "Hello I'm a raw sentence",
    }
    model = RawSentence(**data_point)
    print(model)
    # id=UUID('4a3f61a9-8e75-4341-b3a0-3e64e0b60fb6') text='Hello Im a raw sentence'
    print(model.id)
    # 4a3f61a9-8e75-4341-b3a0-3e64e0b60fb6

    model = RawSentence(**{"id": "", "text": "Hello Im a raw sentence"})
    # model = RawSentence(**{"id": "", "text": 15})
    #   File "pydantic/main.py", line 406, in pydantic.main.BaseModel.__init__
    # pydantic.error_wrappers.ValidationError: 1 validation error for RawSentence
    # id
    #   value is not a valid uuid (type=type_error.uuid)
````

Like with every other class we can define function for this one too. This comes especially
handy with larger classe, that have mutple sub models, but this is a later topic. Here is 
a class function that works with our `text` variable:

````Python
import typing
import uuid
from pydantic import BaseModel


class RawSentence(BaseModel):
    id: uuid.UUID  # An id has to match a UUID
    text: str  # The text has to match a normal str

    def filter_text_by_token_length(self, min_lenth: int) -> typing.List[str]:
        return [
            token
            for token in self.text.split()
            if len(token) >= min_lenth
        ]


if __name__ == "__main__":
    data_point = {
        "id": "4a3f61a9-8e75-4341-b3a0-3e64e0b60fb6",
        "text": "Hello I'm a raw sentence",
    }
    model = RawSentence(**data_point)
    filterd_tokens = model.filter_text_by_token_length(min_lenth=2)
    print(filterd_tokens)
    # ['Hello', "I'm", 'raw', 'sentence']

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
import typing
from pydantic import BaseModel


class Related(BaseModel):
    name: str


class Product(BaseModel):
    price: typing.Union[int, float]
    flag: typing.Optional[str]
    tags: typing.List[str]
    related: typing.Optional[typing.Dict]
    model: typing.Literal["A", "B", "C", "D"]
    related_model: Related
```

You can run this code as is, which can be used like so:

```Python
if __name__ == "__main__":
    product = Product(
        **{
            "price": 1,
            "tags": ["awesome"],
            "model": "A",
            "related_model": {"name": "ChildName"},
        }
    )
    print(product)
    # price=1 flag=None tags=['awesome'] related=None model='A' related_model=Related(name='ChildName')
    print(product.related_model)
    # name='ChildName'
```

# Custom validation

In case we have some non-standard data type we can also use custom data validation. 
For example, we could `from pydantic import HttpUrl`. This allows us to parse and validate
something like `https://arrrrrmin.netlify.com/`. If we'd have a response from some 
aws service recieved by FastAPI, we should be able to validate something like 
`s3://bucket/folder/file.json`, which fails with `HttpUrl`. The following validator can 
handle this:

```Python
# Write a validator function that raises a ValueError (which will be caught inside
# pydantic and returned as a ValidationError, layouting exaktly what went wrong, while
# trying to create the model).

import typing
from pydantic import BaseModel, root_validator, validator


def validate_s3_scheme(s3_uri: str) -> str:
    prefix: str = "s3://"
    if not s3_uri.startswith(prefix):
        raise ValueError("S3 URIs must start with {0}".format(prefix))
    return s3_uri


def validate_non_key_file_string(v: str):
    if len(v) < 1 or "." in v:
        raise ValueError(
            "Length provided should support at least 1 character and it's "
            "not allowed to contain '.'"
        )
    return v


class S3Uri(BaseModel):
    uri: str
    scheme: str = "s3"  # prefix has to be s3://
    bucket: typing.Optional[str]  # the host bucket
    path: typing.Optional[str]  # suffix after bucket
    key: typing.Optional[str]  # file key

    # Use @validator defined below
    _validate_bucket = validator("bucket", allow_reuse=True)(validate_non_key_file_string)
    _validate_path = validator("path", allow_reuse=True)(validate_non_key_file_string)

    # Please note: root validators are always executed on model creation
    @root_validator
    def validate_root_uri(cls, values):  # noqa: U100
        # Most of time you won't use cls, so make sure it doesn't break linting
        uri: str = validate_s3_scheme(values.get("uri"))
        uri_parts: typing.List[str] = uri.split("/")
        # Expect: uri_parts = ["s3:", "", "bucket_name", "folder_name", "key_file.json"]
        uri_length: int = len(uri_parts)
        if uri_length < 3 and len(uri_parts[2]) > 0:
            raise ValueError(
                "S3 URIs must provide at least a bucket. Failed with uri: {0}".format(uri)
            )
        values["bucket"] = uri_parts[2]
        if uri_length > 3:
            values["path"] = "/".join(uri_parts[3:])
        if "." in uri_parts[-1]:
            values["key"] = uri_parts[-1]
        return values

    @validator("key")
    def validate_non_key_file_string(cls, v: str):  # noqa: U100
        # Here we always need a "." in key file string
        if len(v) < 1 or "." not in v:
            raise ValueError(
                "Length provided should support at least 1 character and has to contain "
                "file suffix with '.'"
            )
```

You can run this code as is, which can be used like so:

```Python
        return v


if __name__ == "__main__":
    s3_uri = S3Uri(uri="s3://bucket/folder/key.json")
    print(s3_uri.uri)
    # uri='s3://bucket/folder/key.json' scheme='s3' bucket='bucket' path='folder/key.json' key='key.json'
```

Ok, let's break it down a bit. First we declared what we need and took advantage of 
`typing.Optional`.

```Python
class S3Uri(BaseModel):
    uri: str
    scheme: str = "s3"  # prefix has to be s3://
    bucket: typing.Optional[str]  # the host bucket
    path: typing.Optional[str]  # suffix after bucket
    key: typing.Optional[str]  # file key

```

Our parameters `bucket`, `path` and `key` are optional at first, but will be filled when 
their values become available in `root_validator`, which is the first validator executed, 
by pydantic. With `validate_root_uri` we inspect all `values` recieved by `S3Uri`. We
break it into pieces and fill our optional parameters. By nature an S3Uri needs a bucket, 
which we'll enforce here:

```Python
        # Most of time you won't use cls, so make sure it doesn't break linting
        uri: str = validate_s3_scheme(values.get("uri"))
        uri_parts: typing.List[str] = uri.split("/")
        # Expect: uri_parts = ["s3:", "", "bucket_name", "folder_name", "key_file.json"]
```

Everything else below is just to see wether or not our parsed vales fullfill what we 
expect, such that these are prompted like pydantic intends to.

# Aliases

In some cases, for example working with FastAPI it's useful to work with aliases. Aliases
will help to have [PEP8](https://www.python.org/dev/peps/pep-0008/) (snake-case) 
compatible names, by also support camel-case naming, when creating the model. Here is an
example: 

```Python
import uuid
from pydantic import BaseModel


def to_camel(string: str) -> str:
    return "".join(word.capitalize() for word in string.split("_"))


class Scheme(BaseModel):
    class Config:
        alias_generator = to_camel


class ResponseScheme(Scheme):
    user_id: uuid.UUID
    document_id: uuid.UUID


if __name__ == "__main__":
    response_scheme = ResponseScheme(
        **{"UserId": uuid.uuid4(), "DocumentId": uuid.uuid4(),}
    )
    print(response_scheme.json())
    # {"user_id": "489bee33-7f7e-4b09-b83b-2d44ebeffde6", "document_id": "5e47e30d-d175-457d-8737-84cd06eae3f0"}

```

Like this it's possible to use snake- and camel-case naming when passing data. There is a 
lot more to explore at [Pydantic documentation](https://pydantic-docs.helpmanual.io).


# Configs

Another nice feature: `BaseSettings`. Configurations can be added and validated using 
pydantics `BaseSettings`. In addition one can install `pip install pydantic[dotenv]`, to 
read settings from a `.env` file. This comes in especially handy when building a fastapi.

```Python
import os
from typing import Optional

from pydantic import BaseSettings


class S3Settings(BaseSettings):
    REGION: Optional[str] = os.getenv("REGION") or "eu-central-1"
    MAIN_BUCKET: Optional[str] = os.getenv("MAIN_BUCKET") or None
    USER_BUCKET: Optional[str] = os.getenv("USER_BUCKET") or None

    class Config:
        env_file = ".env.dev.s3"
        env_file_encoding = "utf-8"

```

# Secrets

Building APIs often includes Secrets, which under no circumstances should be leaked. Therefore
pydantic provides `SecretStr` class, which is nice to be sure that secret values are only 
viewable if really needed. The following example reads a secret from AWS Secretsmanager, using
`boto3` in a `root_validator` and holds it in a `BaseSetting` class.

```Python
import base64
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseSettings, SecretStr, root_validator


def read_public_key(secret_name: str, secrets_region_name: str) -> SecretStr | None:
    # See https://boto3.amazonaws.com/v1/documentation/api/latest/guide/secrets-manager.html
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager", region_name=secrets_region_name
    )
    secret = None
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "DecryptionFailureException":
            raise e
        # Catch other errors here ...
    else:
        if "SecretString" in get_secret_value_response:
            secret = get_secret_value_response["SecretString"]
        else:
            secret = base64.b64decode(get_secret_value_response["SecretBinary"])
    # Trying to pass None into SecretStr will result in a ValueError, so validation can happen
    return SecretStr(secret)


class SecretSettings(BaseSettings):
    SECRET_REGION: Optional[str] = os.getenv("SECRET_REGION") or "eu-central-1"
    PRIVATE_KEY: Optional[SecretStr] = None
    PUBLIC_KEY: Optional[SecretStr] = None

    @root_validator
    def val_private_key(cls, values: Dict):  # noqa
        private_key_secret = (
            read_public_key(
                secret_name="SECRETS_NAME_PRIVATE_KEY",
                secrets_region_name=values["SECRET_REGION"],
            )
            or None  # Used to trigger ValueError
        )
        public_key_id_secret = (
            read_public_key(
                secret_name="SECRETS_NAME_PUBLIC_KEY",
                secrets_region_name=values["SECRET_REGION"],
            )
            or None  # Used to trigger ValueError
        )
        return {
            "PRIVATE_KEY": private_key_secret,
            "PUBLIC_KEY": public_key_id_secret,
        }

    class Config:
        env_file = ".env.dev.cf"
        env_file_encoding = "utf-8"


settings = SecretSettings()
print(settings.PRIVATE_KEY)
# SecretStr('**********')
print(settings.PRIVATE_KEY.get_secret_value())
# -----BEGIN RSA PRIVATE KEY-----<...>==-----END RSA PRIVATE KEY-----

```



