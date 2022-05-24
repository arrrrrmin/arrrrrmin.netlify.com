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
