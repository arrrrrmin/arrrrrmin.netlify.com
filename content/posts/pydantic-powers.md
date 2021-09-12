---
title: Pydantic powers
date: 2021-08-21 12:22.214030
draft: false
summary: "Some awesome tips and tricks one can do with pydantic. Data validation with pydantic and never load json without pydantic anymore. Example usage with boto3 (aws sdk for python)."
---

This is my personal though and development bubble, so let's talk [Pydantic](https://github.com/samuelcolvin/pydantic)! Since I first used [FastAPI](https://github.com/tiangolo/fastapi) I'm a huge fan of [Pydantic](https://github.com/samuelcolvin/pydantic). Basically it's about data validation. As developer it's often about recieving data from somewhere, doing something with it and passing it on to some other service or database.

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
- Validate data passed to the model (this is done _on the fly_)
- Enjoy your easily implemented data shape 🎉

This is how to define a model with standard python type hinting:

````Python
# Define the expected model
class RawDataSentence(BaseModel):
	id: UUID  # An id has to match a UUID
	text: str  # The text has to match a normal str

if __name__ == "__main__":
	data_point = {
		"id": "4a3f61a9-8e75-4341-b3a0-3e64e0b60fb6",
		"text": "Hello Im a raw sentence",
	}
	model = RawDataSentence(**data_point)  # Load data in a model
	# Enjoy your easily implemented data shape 🎉
	print(model.id)
	# Do something with it
	filtered_tokens = [
		token for token in model.text.split()
		if len(token) > 2
	]
	print(filtered_tokens)
````

If you we'd load an id like `"id": "not-a-uuid"` pydantic would raise an `ValidationError`. This gives us a high security that our data will match the expected shape.

# Make models more flexible

One can also work with import from `typing`. I often use the following:

- `Union`: On of the passed types must be fulfilled
- `Optional`: Not required
- `List`: is a list of passed types
- `Dict`: is a dictionary
- `Literal`: One of the following strings is allowed

In case of `Dict` one can also build a new pydantic model and pass it as a type to the parent model. Like this it's possible to validate children as well since `**` would be implicit in these cases.

```Python
class Product(BaseModel):
    price: Union[int, float]
    flag: Optional[str]
    tags: List[str]
    child: Dict
    model: Literal["A", "B", "C", "D"]
    modification: Optional[Literal]  # use multiple
```

# Custom validation

If we have some non-standard data we can also use custom data validation. For example we could `from pydantic import HttpUrl`. This allows us to parse and validate something like `https://arrrrrmin.netlify.com/`. If we'd have a response from some aws service recieved by FastAPI, we should be able to validate something like `s3://bucket/folder/file.json`, which fails with `HttpUrl`. The following validator can handle this:

```Python
# Write a validator function that raises some Error/Exception in false cases
def validate_s3_uri(s3_uri: str) -> str:
	prefix = "s3://"
	if not s3_uri.startswith(prefix):
		raise ValueError("S3 URIs must start with {0}".format(prefix))
	return s3_uri


class AWSResponse(BaseModel):
	lastModified: datetime
	name: str
	s3uri: str

	# Validator executed
	_val_s3uri = validator("s3uri", allow_reuse=True)(validate_s3_uri)
```
