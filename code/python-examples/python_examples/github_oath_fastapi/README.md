--- 
title: Github OAuth with FastAPI 
date: 2021-07-23 12:22.214030
draft: false
summary: "An isolated example to show github authorization-code oauth flow in fastapi for web application flow + simple HttpBearer route dependency. This example can be used for all providers of code-based oauth authorization patterns."
weight: -1
---

In a recent project I had to add githubs code-based oauth to an API. To solve this I 
wanted to have a little more insight into, how FastAPI supports developers with this 
process.

## create some github oauth app

* Log into github
* Settings > Developer Settings > Oauth Apps > New oauth App
* Fill out the form
  * `<some-name>`
  * `http://localhost:8000`
  * `<some-description>`
  * `http://localhost:8000/auth/login`
* Generate a ClientSecret (and don't paste it anywhere)
* Copy `ClientID` & `ClientSecret`
* Add your required scopes from [https://docs.github.com/](https://docs.github.com/en/developers/apps/building-oauth-apps/scopes-for-oauth-apps)
* Put it into and `.env`
* Take a look at the github documentation @ [https://docs.github.com/](https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app)

## web application flow

> The device flow isn't covered here at all. This example shows a simple web application 
> flow using fastapis onboard utilities.

* Request user permissions for provided scopes (`/auth/request`)
  * Let your user authenticate the github oauth app permission request
  * Github will forward to your `CALLBACK_URL` (`/auth/login`)
* Recieve code from github and use it to provide the satisfied `acces_token` (`/auth/login`)
* Use the recieved `acces_token` from step 2 to verify it using the Github API 
  * Output look like: `{"Id":<UserId>,"Login":"<GithubLogin>","Token":"<UserToken>","Message":"Happy hacking :D"}`

````Python
{! https://raw.githubusercontent.com/arrrrrmin/fastapi-github-oauth/main/app/main.py [ln:45-55] !}
````

## securing routes with a dependency
* Use `HttpBearer`, to bear the token and use it as dependency for our routes
* These routes are only accessible for authenticated users (requests with valid `access_token`) 
* See the example with `secure/content`

The dependency looks like following:

````Python
{! https://raw.githubusercontent.com/arrrrrmin/fastapi-github-oauth/main/app/main.py [ln:58-] !}
````

See the full source at [app/main.py](https://github.com/arrrrrmin/fastapi-github-oauth/blob/main/app/main.py)


The route parameter `user` is proivded by `Depends(auth.authorized_user)` and has to pass 
`helpers.AuthorizedResponse`s pydantic validation. So in this single line wraps a lot of 
handy functionality: 
* the function `authorized_user` will check whether a passed `token: HTTPAuthorizationCredentials` is valid
* this validation is done by *asking* Githubs OAuth API.
* If the validation in `Depends(...)` is not met `authorized_user` will return an `401` (Not Authorized) response.

The whole code to handle this process look the following in FastAPI (everything behind 
`Depends(...)`, to secure subsequent routes as well):
  
````Python
{! https://raw.githubusercontent.com/arrrrrmin/fastapi-github-oauth/main/app/auth/github.py !}
````

See the full source at [app/auth/github.py](https://github.com/arrrrrmin/fastapi-github-oauth/blob/main/app/auth/github.py)

With the class above we can depend on certain functions to secure our routes. For example,
when we depend on `get_user_data` we need to pass a token, which is validated by github 
and returns valid user data, return by githubs api.
