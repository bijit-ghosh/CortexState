# Installable CortexState SDKs

## Python

From the repository, run `python -m pip install .`, or build a wheel with `python -m pip wheel --no-deps --wheel-dir dist .`. This base package needs no Rust toolchain and always has the pure-Python reference scorer. To add the optional native scorer, build/install the matching `cortexstate-rank` wheel from the CI package artifact; native wheels are specific to the Python version and operating system. When installed, the Rust scorer is selected automatically. Set `CORTEXSTATE_PYTHON_RANKER=1` before Python starts to force the reference implementation.

The package includes the engine, API client, CLI, and dashboard assets. `from cortexstate import Memory, Scope, Client` supports both embedded and service-based use. The optional `[openai]` extra enables the bundled provider adapter.

## JavaScript / TypeScript

```bash
cd sdk/javascript
npm pack
```

Install the generated archive in your application: `npm install /path/to/cortexstate-client-0.4.0.tgz`. Import `CortexState` from `cortexstate-client`. The ESM package includes TypeScript declarations, no runtime dependencies, and named methods for memory, deployment outcomes, lesson candidates, evaluations, and approvals. Node.js 20+ is required.

## Package artifacts and public registries

The **Build and release CortexState packages** GitHub Actions workflow builds the Python wheel/source archive, JavaScript tarball, and optional Rust wheels for Python 3.10/3.12 across Linux, Windows, and macOS runners. When a matching versioned GitHub release is published, it attaches those files to that release; on manual dispatch, it uploads them as workflow artifacts. It does not publish to PyPI/npm.

Public registry release requires owner accounts, verified email, required authentication, an available package name, and publisher configuration. The names in this source are proposed package names, not a reservation or a claim of registry ownership. Do not install an unrelated registry package merely because its name matches.

Create owner accounts at [PyPI](https://pypi.org/account/register/) and [npm](https://www.npmjs.com/signup), complete verification and required authentication yourself, then configure your publisher. Never paste passwords, OTPs, recovery codes, or publishing tokens into issues or chat. Account creation and registry publication are separate from the tested source and package artifacts.
