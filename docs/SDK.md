# Installable CortexState SDKs

## Python

From the repository, run `python -m pip install .`, or build a wheel with `python -m pip wheel --no-deps --wheel-dir dist .`. This base package needs no Rust toolchain and always has the pure-Python reference scorer. To add the optional native scorer, build/install the matching `cortexstate-rank` wheel from the CI package artifact; native wheels are specific to the Python version and operating system. When installed, the Rust scorer is selected automatically. Set `CORTEXSTATE_PYTHON_RANKER=1` before Python starts to force the reference implementation.

The package includes the engine, API client, CLI, and dashboard assets. `from cortexstate import Memory, Scope, Client` supports both embedded and service-based use. The optional `[openai]` extra enables the bundled provider adapter.

## JavaScript / TypeScript

```bash
cd sdk/javascript
npm pack
```

Install the generated archive in your application: `npm install /path/to/cortexstate-client-0.3.0.tgz`. Import `CortexState` from `cortexstate-client`. The ESM package includes TypeScript declarations, no runtime dependencies, and named methods for memory, statistics, proposals, and answers. Node.js 20+ is required.

## Package artifacts and public registries

The **Build SDK packages** GitHub Actions workflow builds a Python wheel/source archive and npm tarball on demand or on a version tag, then uploads them as workflow artifacts. It does not publish to PyPI/npm automatically.

Public registry release requires owner accounts, verified email, required authentication, an available package name, and publisher configuration. The names in this source are proposed package names, not a reservation or a claim of registry ownership. Do not install an unrelated registry package merely because its name matches.

Create owner accounts at [PyPI](https://pypi.org/account/register/) and [npm](https://www.npmjs.com/signup), complete verification and required authentication yourself, then configure your publisher. Never paste passwords, OTPs, recovery codes, or publishing tokens into issues or chat. Account creation and registry publication are separate from the tested source and package artifacts.
