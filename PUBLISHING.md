# Publishing Simple Agent

## Prerequisites

1. Account on PyPI (https://pypi.org)
2. API token from PyPI
3. `uv` or `twine` installed

## Building the Package

```bash
# Clean previous builds
rm -rf dist/

# Build the package
uv build
```

This creates:
- `dist/simple_agent-0.1.0.tar.gz` (source distribution)
- `dist/simple_agent-0.1.0-py3-none-any.whl` (wheel)

## Testing Locally

Before publishing, test the package locally:

```bash
# Install in a virtual environment
uv venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate
uv pip install dist/simple_agent-0.1.0-py3-none-any.whl

# Test the command
agent --help
```

## Publishing to Test PyPI (Recommended First)

```bash
# Using twine
pip install twine
twine upload --repository testpypi dist/*

# Then test install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ simple-agent
```

## Publishing to PyPI

```bash
# Using twine
twine upload dist/*

# Or using uv (if supported)
uv publish
```

## Version Bumping

Before publishing a new version:

1. Update version in `simple_agent/__init__.py`
2. Update version in `pyproject.toml`
3. Create a git tag: `git tag v0.1.0`
4. Push tags: `git push --tags`

## Installation Verification

After publishing, users can install with:

```bash
pip install simple-agent
# or
uv pip install simple-agent
```
