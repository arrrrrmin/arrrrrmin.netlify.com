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
