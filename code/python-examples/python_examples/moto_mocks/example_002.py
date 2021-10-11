# In a real project this file is called "conftest.py"

import typing

import boto3
import pytest
from moto import mock_s3


@pytest.fixture(scope="module")
def default_bucket():
    yield "process-bucket"


@pytest.fixture(scope="module")
def default_file_name():
    yield "required-file.txt"


@pytest.fixture(scope="function")
def file_in_bucket(default_bucket: str, default_file_name: str) -> None:
    file_content: str = "Hello from file_in_bucket() and moto!"
    with mock_s3():
        conn = boto3.resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=default_bucket)
        s3 = boto3.client("s3", region_name="us-east-1")
        response = s3.put_object(
            Bucket=default_bucket, Key=default_file_name, Body=file_content,
        )
        yield


# In a real project this file is called "test_<some-file-or-case>.py"


def test_file_in_bucket(file_in_bucket: typing.Any):
    conn = boto3.resource("s3", region_name="us-east-1")
    body = (
        conn.Object("process-bucket", "required-file.txt")
        .get()["Body"]
        .read()
        .decode("utf-8")
    )
    assert body == "Hello from file_in_bucket() and moto!"
