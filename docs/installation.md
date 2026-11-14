# Installation

This page takes you from an empty folder to a working import. If you already have a project with its own virtual environment, skip to [Install the package](#install-the-package).

## Requirements

- Python 3.10 or newer. Check with `python --version` (on Windows, `py --version`).
- Network access to the Hostinger API from the machine that runs your code.
- An account with Hostinger and API credentials. Hostinger uses an API token created in hPanel. See [](credentials.md).

The package pulls in four dependencies, all installed for you:

| Package | Why it is needed |
| --- | --- |
| [httpx](https://www.python-httpx.org/) | Sends the HTTP requests, both sync and async. |
| [goodconf](https://github.com/lincolnloop/goodconf) | Loads settings from code, environment variables and files. |
| [pydantic](https://docs.pydantic.dev/) | Validates the settings. |
| [PyYAML](https://pyyaml.org/) | Reads the message catalogue and YAML config files. |

## Create a virtual environment

A virtual environment keeps the SDK and its dependencies separate from the Python that came with your system. Create one inside your project folder.

::::{tab-set}

:::{tab-item} Linux and macOS
```bash
mkdir dns-tools
cd dns-tools
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt now starts with `(.venv)`. Run `deactivate` to leave it, and `source .venv/bin/activate` again whenever you open a new terminal.
:::

:::{tab-item} Windows (CMD)
```bat
mkdir dns-tools
cd dns-tools
py -m venv .venv
.venv\Scripts\activate.bat
```

Your prompt now starts with `(.venv)`. Run `deactivate` to leave it, and `.venv\Scripts\activate.bat` again whenever you open a new CMD window.
:::
::::

## Install the package

::::{tab-set}

:::{tab-item} pip
```bash
pip install hostinger-python-sdk
```
:::

:::{tab-item} uv
```bash
uv add hostinger-python-sdk
```

Outside a uv project, `uv pip install hostinger-python-sdk` installs it into the active environment.
:::

:::{tab-item} Poetry
```bash
poetry add hostinger-python-sdk
```
:::
::::

The distribution is called `hostinger-python-sdk`, but you import it as `hostinger_sdk`:

```python
from hostinger_sdk import Hostinger
```

## Optional extras

Configuration files in JSON work out of the box. Two extras add the other formats:

| Extra | Adds | When you need it |
| --- | --- | --- |
| `yaml` | YAML support in goodconf | You keep settings in `hostinger.yaml` or `hostinger.yml`. |
| `toml` | TOML support in goodconf | You keep settings in `hostinger.toml` and run Python 3.10. Python 3.11 and newer read TOML without it. |

```bash
pip install "hostinger-python-sdk[yaml]"
pip install "hostinger-python-sdk[toml]"
pip install "hostinger-python-sdk[yaml,toml]"
```

The quotes stop shells like zsh from treating the square brackets as a pattern.

## Check the install

```bash
python -c "import hostinger_sdk; print(hostinger_sdk.__version__)"
```

It prints the installed version, for example `0.1.0`. A `ModuleNotFoundError` usually means the virtual environment is not active, or the package went into a different Python than the one you are running.

You can also check that the client can be built without touching the network. Building a client only reads the settings, it does not send a request:

```python
from hostinger_sdk import Hostinger

client = Hostinger("API_TOKEN")
print(client)
```

## Pin the version

The SDK follows semantic versioning. Until 1.0, a minor release (0.1 to 0.2) may change the API, so pin the minor version in applications:

```text
hostinger-python-sdk>=0.1,<0.2
```

## Upgrade

```bash
pip install --upgrade hostinger-python-sdk
```

Read the [changelog](changelog.md) before moving to a new minor version.

## Uninstall

```bash
pip uninstall hostinger-python-sdk
```

This leaves the dependencies (httpx, goodconf, pydantic, PyYAML) in place, since other packages may use them. Delete the `.venv` folder to remove everything at once.

## Install from source

To try the latest code from GitHub, or to work on the SDK itself:

```bash
git clone https://github.com/qiyascc/hostinger-python-sdk.git
cd hostinger-python-sdk
pip install -e ".[dev]"
```

See [](development.md) for running the tests.
