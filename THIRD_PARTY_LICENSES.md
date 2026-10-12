# License and dependency notes

**Source revision reviewed:** `bf281f1d68e9e6af44db9d12588a000fac531a61`
**Package version:** `0.3.0`
**Project license:** [MIT](LICENSE), with attribution in [NOTICE](NOTICE)

This file summarizes declared direct project dependencies and selected upstream license information. It is not a generated SBOM, a complete transitive dependency audit, or a legal review of every way the software may be combined or distributed. Build and test tools can resolve to different versions because the project declares version floors rather than a lockfile.

## Declared package scopes

| Component | Scope in this project | Declaration or observation | License information |
|---|---|---|---|
| USMC | Project source and package | `pyproject.toml`; version `0.3.0` | MIT; see `LICENSE` and `NOTICE`. |
| Python standard library | Runtime environment, including `sqlite3` | Python `>=3.10` | Python distributions include PSF license information; details depend on the Python distribution. |
| setuptools | Build backend | `setuptools>=77` | Check the resolved backend distribution's license files for the build in use. |
| pytest | Test extra | `pytest>=7.0`; observed metadata in this review: 8.3.4, MIT | [pytest project](https://github.com/pytest-dev/pytest) and its resolved distribution metadata. |
| Ruff | Test extra | `ruff>=0.1.0`; observed metadata in this review: 0.16.8, MIT | [Ruff project](https://github.com/astral-sh/ruff) and its resolved distribution metadata. |
| tomli | Test extra on Python <3.11 | `tomli>=2.0; python_version < '3.11'` | Check the resolved distribution metadata and [tomli project](https://github.com/hukkin/tomli). |

`pyproject.toml` declares no direct runtime package dependencies. It does not declare `wheel` as a build requirement. Python itself, build isolation, pip, Git, and test tools have scopes outside the runtime dependency list.

## Network and runtime scope

The package's declared runtime dependency list is empty, but this does not make installation or builds network-free. Installing from Git or resolving a build backend may use network access. The reviewed USMC package modules contain no direct HTTP client; this source review does not audit the host, Python distribution, build tools, or calling processes.

## License references

- Project license: [`LICENSE`](LICENSE)
- Project attribution: [`NOTICE`](NOTICE)
- Python license information: https://docs.python.org/3/license.html
- setuptools license and notices: https://github.com/pypa/setuptools
- pytest license and notices: https://github.com/pytest-dev/pytest
- Ruff license and notices: https://github.com/astral-sh/ruff
- tomli license and notices: https://github.com/hukkin/tomli

The companion [plain-text notes](THIRD_PARTY_LICENSES.txt) use the same limited scope.
