---
title: OAuth at cloudfront
date: 2022-02-08 10:26.214030
draft: false
summary: "A simple solution to secure cloudfront distributions via lambda@edge"
weight: -5
---

During a recent project I came accross a common problem when handling content in a frontend. 
The situation is pretty common, content is stored sowhere on S3 in some structure and users
should be able to access it quickly, but only for authorized individuals. 
Meaning there should be some sort of authentication using some Identity Provider (IDP).
In adition the access control should be able to support grouping to bundle access rights 
for the content. 

> [**TL;DR Just give me code**](https://github.com/arrrrrmin/cloudfront-cognito-auth)

![Overview](/oauth_at_cloudfront.png)

The articles approach uses cookies to store tokens, which are validated using a lambda@edge. 
Maybe that's the better approach to take. For my usecase it's ok to send an access token in 
the header, for every request. The only relevant thing was: Requests should be cached by 
Cloudfront as long as the validation succeeds.

# Basic solution

As shown in the overview diagram the solution is constructed, using the following service 
components:
* Store assets in a secure S3 bucket (default settings, no public access)
* Fast access to assets on the S3 origin using Cloudfront Distributions as CDN
* Authentication via OAuth with lambda@edge

On S3 there's not alot to talk about, just create a bucket with default settings, which
blocks all public access. This is what we want, check. Assets should be accessed via 
Cloudfront. This enables *low latency and high transfer speeds*. For Cloudfront pricing
take a look at [this](https://aws.amazon.com/cloudfront/pricing/) overview.

# S3 & Cloudfront

In order to link S3 to your Cloudfront CDN, just create a distribution that resolves the
S3 bucket as the distribution's origin. For now there's no lambda function to secure our
CDN, meaning when you access `<dist-url>/path/to/your/ressource-on-bucket.png`, you get a 
response. Ok, now the S3 bucket is effectivly public. Now we need an easy way to secure
content on the bucket.

# Cognito

Now we can't verify the authorization of user. We have no identity provider, to create
identities for us. There are many IDPs e.g.: Github, Google, .... Most providers use
OAuth2 as authentication flow. An authentifaction flow is basically the process in which 
an individual proofs the identity to the provider, which involves some process of
verification. In case you want to go all the way on this topic see the spec 
[rfc6750](https://datatracker.ietf.org/doc/html/rfc6750).

So Cognito is our identity provider which creates identities for our users, which we can 
verify by decoding tokens with encryption information (public keys) we obtain from cognito.
Like this we can identify an individual as a member of our user pool or group and thus
grant or deny access to resources.

# Lambda@edge

Since our distribution exposes the bucket now, we need a security layer on top of this.
Here is where lambda@edge comes in. The name tells what it does, executing a lambda 
function close at the edge of network. There are a few limitations for an edge function:
* Lambda has to be in `us-east-1` (US East, N. Virginia)
* *You can’t configure your Lambda function to access resources inside your VPC*
* Edge function and distribution must be owned by the same AWS account
* Function code and dependencies (zip) must be `< 10MB`

The first step is always to find a sample of the event the function has to handle. In 
this case the following can be used:
````json
{! ./python_examples/oauth_at_cloudfront/sample_event.json !}
````
So the first thing we're interested in is the request header. There's our authentication 
head. For getting started with how such an HTTP header could look like see
[Mozillas Web/HTTP/Authentication](https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication).
In our example we want to work with cognito as IDP, since we're on AWS anyways. Since
we'll obtain some tokens (access, id & refresh token (OAuth2)) from cognito we'll need the 
`Bearer` authentication scheme. At this point we already passed the authentication flow with 
username/password in the frontend and obtained an access token from cognito, which is sent to
cloudfront in the header. The example show that too. You just need to exchange `Bearer <token>`
with the actual token.

## Check the header

So let's check if the header is structured the way we expect:

````Python
{! ./python_examples/oauth_at_cloudfront/example_001.py [ln:130-146] !}
````
In the example you can see we expect the header to include an authorization part where we 
also need a bearer followed by the token, split by a blank.

## Verify the token

If you want to know more about the JWT token you obtained by cognito, go to 
[jwt.io](https://jwt.io/) and test their debugger. Don't worry the token will never leave
jwt.io's client side. So decoding is done completely in the frontend. I'm not as much into
tooling on that topic, but jwt.io is the only place I would paste a token.
Anyways when you use their debugger, you'll see that there are different parts this token 
consist of.
* Token header
* Token payload (data)
* Tokens verify signature

All the token parts are split by `.` in the token string and contain different information.
The header contains `kid` (key id) and the encryption algorithm e.g. `RS256`.
To verify if a token comes from our identity provider we take information the IDP gives us 
and decode the token. So you need the following parameters of your user pool:
* Region
* User pool id
* Client id

Imho the actual decoding should be left to the pros who know what they do - and everybody
is lazy anyways. So `python-jose` is the way to go for decoding JWT tokens. For more detail
see the [`python-jose github-repo`](https://github.com/mpdavis/python-jose).
I came across `python-jose` trying to implement verification with `pycognito`. A nice 
project handling the cognito oauth flow for you. Downside was that it's already too large 
for the usecase in lambda@edge, since the bundled package doe not pass lambda@edge's 10 MB 
restriction. So I went forward taking just the parts required for decoding the access_token.
If you want to see where the `TokenVerifier` code came from have a look at
[`pycognito`](https://github.com/pvizeli/pycognito).

````Python
{! ./python_examples/oauth_at_cloudfront/example_001.py [ln:57-127] !}
````

The decoded token returned by `verify_token(...)` will be a dictionary, which will hold
key-value pairs (decoded token content). At this point we already have everything we want.
A header check, token verification and decoding. Everythin we now need to do is further check
the tokens content. This could look like this:

````Python
{! ./python_examples/oauth_at_cloudfront/example_001.py [ln:43-54] !}

{! ./python_examples/oauth_at_cloudfront/example_001.py [ln:149-167] !}
````

## Further checks

The only thing missing from here on is specific checks, based on the request compaired to the
passed token. Here one can do different things here some examples:
* Match `sub` (subject) and match it to requested `uri`
* Match `cognito:group` and match it to requested `uri`
* Match `cognito:<custom-attribute>` and match it to requested `uri` 

Some ideas:

````Python
{! ./python_examples/oauth_at_cloudfront/example_001.py [ln:175-182] !}
````

# Wrap it up

Lastly we remove the Authentication header, so Cloudfront can handle the request itself,
by passing the input request back to Cloudfront.

````Python
{! ./python_examples/oauth_at_cloudfront/example_001.py [ln:185-189] !}
````

Here is what the `lambda_handler(...)` looks like:

````Python
{! ./python_examples/oauth_at_cloudfront/example_001.py [ln:34-41] !}
{! ./python_examples/oauth_at_cloudfront/example_001.py [ln:190-221] !}
````

With the `REDIRECT_302` response, cloudfront will redirect users to the `uri` in 
`locations` header. This can be the uri pointing to the cognito hosted-ui or frontends
login page. From there on users can log in, and the authentication flow will start, until
a valid access token is obtained by the user.

