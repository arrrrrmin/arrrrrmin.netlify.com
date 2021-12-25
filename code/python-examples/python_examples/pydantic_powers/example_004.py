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
        return v


if __name__ == "__main__":
    s3_uri = S3Uri(uri="s3://bucket/folder/key.json")
    print(s3_uri.uri)
    # uri='s3://bucket/folder/key.json' scheme='s3' bucket='bucket' path='folder/key.json' key='key.json'