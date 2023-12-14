# HOWTO build and distribute pygramm

We are following procedures from
[the packaging tutorial](
https://packaging.python.org/en/latest/tutorials/packaging-projects/
) which differs significantly from the HitchHikers guide.
You may assume that a good deal of grumbling took place while
finding a workable process.  We hope these instructions
slightly reduce the amount of grumbling you must produce to
build and distribute Pygramm to PyPi. 

Assuming you already are working in a virtual environment,
the build process in a nutshell is: 

## 0. Prep

You need a TestPyPi package name, a PyPi package name, 
recovery codes and API tokens for each, and a .toml file
specifying the project structure.  See the tutorial. 

## 1.  Build new version of the distribution package

Bump the version number in your `pyproject.toml` file,
otherwise you will not be able to push to PyPi or
TestPyPi.  It looks like this: 

```python
version = "0.0.3"
```

```python
python3 -m pip install --upgrade build
python3 -m build
``` 

This should leave a .tar.gz and a .whl file in the
`dist` directory.  If there are more than one of each,
discard the old ones. 

## 2. 

```
python3 -m twine upload --repository testpypi dist/*
```
Use `__token__` for username.  (Yes, really.)  
Use your API token (see the tutorial) for the password. 

