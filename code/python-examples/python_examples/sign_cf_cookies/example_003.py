import base64
import os
from typing import Optional, Dict

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseSettings, root_validator
from pydantic.types import SecretStr


def read_public_key(secret_name: str, secrets_region_name: str) -> SecretStr | None:
    # See https://boto3.amazonaws.com/v1/documentation/api/latest/guide/secrets-manager.html
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=secrets_region_name
    )
    secret = None
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise e
    else:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            secret = base64.b64decode(get_secret_value_response['SecretBinary'])
    return SecretStr(secret)


class CFSettings(BaseSettings):
    CFDOMAIN: Optional[str] = os.getenv("CFDOMAIN") or None
    SECRET_REGION: Optional[str] = os.getenv("SECRET_REGION") or None
    COOKIE_SIGNING_PRIVATE_KEY: Optional[SecretStr] = None
    COOKIE_SIGNING_PUBLIC_KEY_ID: Optional[SecretStr] = None

    @root_validator
    def val_private_key(cls, values: Dict):
        private_key_secret = read_public_key(
            secret_name="BP_COOKIE_SIGNER_PRIVATE_KEY",
            secrets_region_name=values["SECRET_REGION"],
        ) or None
        public_key_id_secret = read_public_key(
            secret_name="BP_COOKIE_SIGNER_PUBLIC_KEY_ID",
            secrets_region_name=values["SECRET_REGION"],
        ) or None
        return {
            "CFDOMAIN": values["CFDOMAIN"],
            "COOKIE_SIGNING_PRIVATE_KEY": private_key_secret,
            "COOKIE_SIGNING_PUBLIC_KEY_ID": public_key_id_secret,
        }


cloudfront_settings = CFSettings()
