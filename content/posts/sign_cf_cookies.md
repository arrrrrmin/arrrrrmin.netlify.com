---
title: Access Cloudfront with signed cookies
date: 2022-05-24 10:56.214030
draft: false
summary: "A short guide on how to secure a cloudfront distribution using signed cookies, based on CF's trusted key groups (including aws-cdk infra)."
weight: -6
---

This article is a short extension of 
[velotios engineering blog post](https://www.velotio.com/engineering-blog/s3-cloudfront-to-deliver-static-asset). 
This post should give a bit more detail to the api side and how to set it up with aws-cdk.

The approach describes how to use Cloudfront distribution with signed cookies, to securely grant access to S3 
resource paths. 
It's an alternative to 
[signing URLs using boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html), 
which are used to grant access on single resources, whereas this example shows how a folder can be accessed easily.

## Overview

![Overview](/overview.png)

The overview image is just a summary and does not include entities like `AppClient`, `PublicKey` or `KeyGroup`.
These are listed and showen below in the [infra setup](#infra-setup)

The only thing we really need to take care of (after handling the infra properly) is to have a route that handles the
user sub and validates the access for this sub, in some way. This can be done, by storing required inforamtion in a 
database and have the API asking, wether or not the requesting sub is authorized to access. The example for this route
using fastapi is shown in the [Sign cookies section](#sign-cookies). 

## Create a key pair

This is pretty simple, just run:

```bash
openssl genrsa -out private_key.pem 2048
openssl rsa -pubout -in private_key.pem -out public_key.pem
```

For more details see [Create a key pair for a trusted key group (recommended)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-trusted-signers.html#create-key-pair-and-key-group).
> **Note**: You can also store this key pair AWS' Secretmanager and retrieve it in your infa and the api, by referencing 
> the secrets name, but don't store them together, since the Infra just needs to know the Public Key Id, 
> not the private key.   

## Infra setup

We'r using [aws-cdk-lib@v2.25.0](https://github.com/aws/aws-cdk) in python to create infra structure for this example:

````Python
import aws_cdk as cdk
import aws_cdk.aws_s3 as aws_s3
import aws_cdk.aws_cognito as aws_cognito
import aws_cdk.aws_cloudfront as aws_cloudfront
from constructs import Construct


class InfraStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
````

* An S3 `Bucket` to store data

````Python
        self.main_bucket = aws_s3.Bucket(
            self,
            "MainBucket",
            bucket_name="main-bucket",
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
        )

        self.main_bucket_oai = aws_cloudfront.S3OriginConfig(
            s3_bucket_source=self.main_bucket,
            origin_access_identity=aws_cloudfront.OriginAccessIdentity(
                self,
                "MainOAI",
                comment="OAI for Main S3 Bucket AccessDistro",
            ),
        )
````

* An Cognito `UserPool` & `AppClient` for user authentication

````Python
        self.main_pool = aws_cognito.UserPool(
            self,
            "UserPool",
            user_pool_name="UserPool",
            self_sign_up_enabled=True,
            auto_verify=aws_cognito.AutoVerifiedAttrs(email=True),
            sign_in_aliases=aws_cognito.SignInAliases(username=True),
            user_verification=aws_cognito.UserVerificationConfig(
                email_subject="Verify your email for our awesome app!",
                email_body="Thanks for signing up to our awesome app! Your verification code is {####}",
                email_style=aws_cognito.VerificationEmailStyle.CODE,
            ),
            standard_attributes=aws_cognito.StandardAttributes(
                email=aws_cognito.StandardAttribute(required=True, mutable=True),
                family_name=aws_cognito.StandardAttribute(required=False, mutable=True),
                given_name=aws_cognito.StandardAttribute(required=False, mutable=True),
                # ...
            ),
            custom_attributes={
                "isAdmin": aws_cognito.BooleanAttribute(mutable=True),
                # ...
            },
            lambda_triggers=aws_cognito.UserPoolTriggers(
                post_confirmation=self.post_confirm_lambda_fn
            ),
        )

        self.main_pool.add_client(
            "WebAppClient",
            user_pool_client_name="WebAppClient",
            auth_flows=aws_cognito.AuthFlow(
                admin_user_password=True,
                user_password=True,
                user_srp=True,
            ),
            id_token_validity=cdk.Duration.minutes(60),
            generate_secret=True,
            o_auth=aws_cognito.OAuthSettings(
                flows=aws_cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[  # noqa
                    aws_cognito.OAuthScope.OPENID,
                    aws_cognito.OAuthScope.COGNITO_ADMIN,
                    aws_cognito.OAuthScope.EMAIL,
                ],
                callback_urls=["http://localhost:8000/v1/auth/verify/"],
                logout_urls=[],
            ),
            prevent_user_existence_errors=False,
            refresh_token_validity=cdk.Duration.days(30),
            # read_attributes (Default: All standard and custom attributes)
            # write_attributes (Default: All standard and custom attributes)
        )
````

* A `KeyGroup` which holds a `PublicKey` for decrypting signed cookies

````Python
        self.keygroup_public_key = aws_cloudfront.PublicKey(
            self,
            "CFPublicKeyCookieSigning",
            public_key_name="CFPublicKeyCookieSigning",
            encoded_key=open("/public_key.pem").read(),
        )
        self.keygroups = [
            aws_cloudfront.KeyGroup(
                self,
                "MainBucketAccessDistroKeyGroup",
                key_group_name="MainBucketAccessDistroKeyGroup",
                items=[self.keygroup_public_key],
            )
        ]
````

* An `CloudFrontWebDistribution` to access bucket resources

````Python
        self.access_distro = aws_cloudfront.CloudFrontWebDistribution(
            self,
            "MainAccessDistro",
            origin_configs=[
                aws_cloudfront.SourceConfiguration(
                    behaviors=[
                        aws_cloudfront.Behavior(
                            allowed_methods=aws_cloudfront.CloudFrontAllowedMethods.ALL,
                            is_default_behavior=True,
                            path_pattern="/",
                            trusted_key_groups=self.keygroups,
                            viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                        )
                    ],
                    s3_origin_source=self.main_bucket_oai,
                )
            ],
        )
````

* (Optionally) An ECS hosted backend API (in our case we just have a locally hosted api)
  * For prod it's a good idea to have all these in the same VPC and have HTTPS only enabled in the CF distribution

## API setup

The API is pretty straight forward:
* [fastapi](https://github.com/tiangolo/fastapi)
* [fastapi-cloudauth](https://github.com/tokusumi/fastapi-cloudauth)
* [boto3](https://github.com/boto/boto3)
* [pydantic](https://pydantic-docs.helpmanual.io)

````Python
import os
from typing import Dict

from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException
from fastapi_cloudauth.cognito import Cognito

from python_examples.sign_cf_cookies.example_004 import sign_cookie
from python_examples.sign_cf_cookies.example_003 import cloudfront_settings

app = FastAPI()
auth = Cognito(
    region=os.environ["REGION"], 
    userPoolId=os.environ["USERPOOLID"],
    client_id=os.environ["APPCLIENTID"]
)


class AccessUser(BaseModel):
    sub: str


@app.get("/access/")
def secure_access(current_user: AccessUser = Depends(auth.claim(AccessUser))):
    # access token is valid and getting user info from access token
    return f"Hello", {current_user.sub}
````

### Obtain secrets

Since the API needs to know about private key and the public key id, we need to pass these as environment variables.
In case we have them stored in secretsmanager, we can collect them like following:
````Python
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

````

Now we have everything in place.
* A infrastructe project with `aws-cdk-lib` (`v2.25.0`)
* An API to check authorization state via JWTs
* Our Secrets passed to API environment via secretsmanager

## Sign cookies

We just need to sign the cookie. Here I'll just paste the code of *Suraj Patil* in his 
[post](https://www.velotio.com/engineering-blog/s3-cloudfront-to-deliver-static-asset):

````Python
import rsa
import datetime
import functools

from typing import Dict
from botocore.signers import CloudFrontSigner
from python_examples.sign_cf_cookies.example_002 import cloudfront_settings


def sign_cookie(resource_path: str) -> Dict:
    # See https://www.velotio.com/engineering-blog/s3-cloudfront-to-deliver-static-asset

    print("Generating cookie to access resource_path:", resource_path)
    # The ID for a CloudFront public key
    CLOUDFRONT_PUBLIC_KEY_ID = (
        cloudfront_settings.COOKIE_SIGNING_PUBLIC_KEY_ID.get_secret_value()
    )
    # Enter datetime for expiry of cookies e.g.:
    EXPIRES_AT = datetime.datetime.now() + datetime.timedelta(hours=2)

    # Load the private key
    key = rsa.PrivateKey.load_pkcs1(
        cloudfront_settings.COOKIE_SIGNING_PRIVATE_KEY.get_secret_value()
    )

    # Create a signer function that can sign message with the private key
    rsa_signer = functools.partial(rsa.sign, priv_key=key, hash_method="SHA-1")

    # Create a CloudFrontSigner boto3 object
    signer = CloudFrontSigner(CLOUDFRONT_PUBLIC_KEY_ID, rsa_signer)

    # Build the CloudFront Policy
    policy = signer.build_policy(resource_path, EXPIRES_AT).encode("utf8")
    CLOUDFRONT_POLICY = signer._url_b64encode(policy).decode("utf8")

    # Create CloudFront Signature
    signature = rsa_signer(policy)
    CLOUDFRONT_SIGNATURE = signer._url_b64encode(signature).decode("utf8")

    return {
        "CloudFront-Policy": CLOUDFRONT_POLICY,
        "CloudFront-Signature": CLOUDFRONT_SIGNATURE,
        "CloudFront-Key-Pair-Id": CLOUDFRONT_PUBLIC_KEY_ID,
    }

````

Now just we can make it accessible in an api route:

````Python
@app.get("/sign_cookies")
def obtain_cookies(
    request_path: str, current_user: AccessUser = Depends(auth.claim(AccessUser))
) -> Dict:
    # Example if further checks are required, sub can be used to validate authorization states
    if current_user.sub != request_path:
        raise HTTPException(401, detail="Unauthorized")
    # Returns signed cookies which authorizes users for a resource in format
    # "{protocol}://{domain}/{sub}/*" for e.g. "https://{distribution}.cloudfront.net/{sub}*"
    return sign_cookie(
        resource_path="{0}/{1}/*".format(
            cloudfront_settings.CFDOMAIN, current_user.sub
        )
    )

````

Since we have `current_user` (which is send by the user in an `Authorization` Header), we can easily obtain an Access
Token, to check if the user is authorized and further use it's `sub` value to make more checks. One example could be:

> Users can grant other users access and these *connections* are maintained in a database. So if a wants to access 
> resources which aren't his own, we can check this by asking the database.



