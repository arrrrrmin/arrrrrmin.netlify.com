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
