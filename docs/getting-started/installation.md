# Installation

Kaj currently runs as a Python package from the source repository. It is not yet presented as a published package installation workflow.

## Requirements

- Python 3.12 or newer
- Git

## Development installation

Clone the repository, create a virtual environment, and install Kaj with its development tools:

```bash
git clone https://github.com/rakin374/kaj.git
cd kaj
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

Verify the command:

```bash
kaj --version
```

You can also invoke the same CLI through Python:

```bash
python -m kaj --version
```

Next: [Quickstart](quickstart.md). For the exact command contract, see the [CLI reference](cli.md).
