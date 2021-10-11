--- 
title: Mocks with moto 
date: 2021-10-08 12:22.214030
draft: false
summary: "Mocking aws services and functionality with moto and pytest."
weight: -3
---

Recently I work with aws infrastructre, so my applications use aws services for infra like
s3 buckets, ecs and so on. Or maybe I got some audio data and need aws transcribe. 
One example could be simulation of a transcription job in aws transcribe, which is 
required, by some application. How can we make sure this transcription job exists and has 
the state we expect it to? Usually this problem comes up when testing the code
becomes important - which btw should be the start of the project. At this point we have a 
few possibilities to handle this requirement for our code.

* *I don't care I know it exists*
* Use [localstack](https://github.com/localstack/localstack) and run tests against vertual localstack in a docker container
* Use [moto](https://github.com/spulec/moto) and mock aws services virtually for your test when you need it

I'm personally not really into localstack, so I am bias here. Nevermind, moto gave me some
fun and covers most of what's needed for us. So let's just take the transcription job 
example to get started. 

With moto this become pretty easy to handle. Moto provides decorators and functions to 
map all boto related calls to motos mocks. Like this it's possible for us to create a 
transcription job, without actually creating one. Moto will mock it for us. So we are not 
hitting an actual endpoint everytime we run tests with a test suit 
(for me it's [pytest](https://github.com/pytest-dev/pytest)). 

# An example

````Python
{! ./python_examples/moto_mocks/example_001.py [ln:1-28] !}
````

Moto's magic comes in at:

````Python
{! ./python_examples/moto_mocks/example_001.py [ln:15-16] !}
````

where a transcription job is started and to check it with pytest `get_transcription_job()`
is called to get the response from the aws transcribe endpoint. Like this we can check a
job was started somewhere in our code. 

> The only thing one has to care about is that `@mock_transcribe` is called befor the 
> `boto.client("transcribe")`-connection is established. If not, 
> [`boto`](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe.html)
> tries to hit the actual endpoint which will fail in integration tests that run in a
> github action.

# Working with `conftest.py`

As mentioned before [pytest](https://github.com/pytest-dev/pytest) is my prefered test 
suit in python, so working with scoped fixtures is mostly done in a file called 
[`conftest.py`](https://docs.pytest.org/en/6.2.x/fixture.html?highlight=conftest#scope-sharing-fixtures-across-classes-modules-packages-or-session).
This file loads injects fixtures for tests in the prefered scope:

## Test scopes

* `function` - the default scope, the fixture is destroyed at the end of the test.
* `class` - the fixture is destroyed during teardown of the last test in the class.
* `module` - the fixture is destroyed during teardown of the last test in the module.
* `package` -the fixture is destroyed during teardown of the last test in the package.
* `session` - the fixture is destroyed at the end of the test session.

So we really want to use this file, to organise fixtures and their availability. An 
example could look like so:

````Python
{! ./python_examples/moto_mocks/example_002.py [ln:3-30] !}
````

In some other test file, you'd uses these, without having to `mock_s3` again (this would
cause the test to fail, because moto is starting a *new mock session*). Use the above 
fixtures like so:

````Python
{! ./python_examples/moto_mocks/example_002.py [ln:36-] !}
````

