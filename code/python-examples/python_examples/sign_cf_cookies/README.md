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

![Overview](/sign_cf_cookies.png)

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
{! ./python_examples/sign_cf_cookies/example_001.py [ln:1-10] !}
````

* An S3 `Bucket` to store data

````Python
{! ./python_examples/sign_cf_cookies/example_001.py [ln:12-26] !}
````

* An Cognito `UserPool` & `AppClient` for user authentication

````Python
{! ./python_examples/sign_cf_cookies/example_001.py [ln:28-79] !}
````

* A `KeyGroup` which holds a `PublicKey` for decrypting signed cookies

````Python
{! ./python_examples/sign_cf_cookies/example_001.py [ln:81-94] !}
````

* An `CloudFrontWebDistribution` to access bucket resources

````Python
{! ./python_examples/sign_cf_cookies/example_001.py [ln:95-112] !}
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
{! ./python_examples/sign_cf_cookies/example_002.py [ln:1-26] !}
````

### Obtain secrets

Since the API needs to know about private key and the public key id, we need to pass these as environment variables.
In case we have them stored in secretsmanager, we can collect them like following:
````Python
{! ./python_examples/sign_cf_cookies/example_003.py !}
````

Now we have everything in place.
* A infrastructe project with `aws-cdk-lib` (`v2.25.0`)
* An API to check authorization state via JWTs
* Our Secrets passed to API environment via secretsmanager

## Sign cookies

We just need to sign the cookie. Here I'll just paste the code of *Suraj Patil* in his 
[post](https://www.velotio.com/engineering-blog/s3-cloudfront-to-deliver-static-asset):

````Python
{! ./python_examples/sign_cf_cookies/example_004.py !}
````

Now just we can make it accessible in an api route:

````Python
{! ./python_examples/sign_cf_cookies/example_002.py [ln:29-] !}
````

Since we have `current_user` (which is send by the user in an `Authorization` Header), we can easily obtain an Access
Token, to check if the user is authorized and further use it's `sub` value to make more checks. One example could be:

> Users can grant other users access and these *connections* are maintained in a database. So if a wants to access 
> resources which aren't his own, we can check this by asking the database.

