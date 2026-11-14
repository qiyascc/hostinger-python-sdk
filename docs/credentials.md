# API token

The Hostinger API uses a single bearer token. The SDK sends it on every request as:

```text
Authorization: Bearer <token>
```

## Create a token

1. Sign in to [hPanel](https://hpanel.hostinger.com).
2. Open the [API page of your profile](https://hpanel.hostinger.com/profile/api).
3. Create a new token and copy it.

A token has the same permissions as the user who created it. If that user can manage a domain in hPanel, the token can manage it through the API, and the other way round. Create the token with an account that owns the domains you want to automate.

## Give it to the SDK

```python
from hostinger_sdk import Hostinger

hs = Hostinger("API_TOKEN")
```

```bash
export HOSTINGER_API_TOKEN=your-token
```

```toml
api_token = "your-token"
```

With the variable or a `hostinger.toml` file in place, `Hostinger()` needs no argument. The token is the first positional argument of the client, or the keyword `token=`:

```python
hs = Hostinger(token="your-token")
```

## Where to keep it

Keep the token out of your source code and out of git.

- In development, an environment variable or a `hostinger.toml` file listed in `.gitignore`.
- On a server, the environment of the service (a systemd `EnvironmentFile`, a container secret, your platform's secret store).
- In CI, the CI system's secret variables.

The settings store the token as a pydantic `SecretStr`, so printing the settings shows `**********`.

Because a token can do whatever its user can, treat it like a password. If one leaks, delete it in hPanel and create a new one.

## Check that it works

Listing the portfolio is a cheap read:

```python
from hostinger_sdk import AuthenticationError, Hostinger

with Hostinger() as hs:
    try:
        domains = hs.domains.list()
    except AuthenticationError:
        print("Hostinger rejected the token")
    else:
        print("Token works,", len(domains), "domain(s) in the portfolio")
```

If no token is found anywhere, building the client raises `AuthenticationError` before any request, with a message that lists every place the SDK looked.
