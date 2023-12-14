# Project organization and packaging

## Why is PyGramm a PyPi package? 

Pygramm is designed for systematic grammar-based fuzzing, and is 
used in both Slackline and Treeline.  We tried initially to maintain 
and distribute it as a git submodule.  We found that very clumsy 
with Python's path management for "import".  The current 
organization follows Python packaging guidelines. 

## References

We are following guidelines from
"[Packaging Python Projetcts](
https://packaging.python.org/en/latest/tutorials/packaging-projects/)".

Note that this differs significantly from guidelines in
[The Hitchikers Guide to Python](
https://docs.python-guide.org/writing/structure/),
which recommends _against_ placing the project in a "src" 
subdirectory. If you go looking for guidelines on organizing and 
distributing Python projects, you will find plenty of contradictory 
advice and a lot of fragile hacks.  It's a problem. It's not a 
problem we have time to fix here. 

## Extending PyGramm

There is a price for packaging PyGramm as a PyPi package rather than 
a Git submodule. If you can use PyGramm _exactly as is_, it is fine. 
If you fork Slackline or Treeline and need to make some extensions 
to Pygramm for your cool grammar-based fuzzing project, it is not 
great.  Instead of also forking PyGramm and continuing to use it as 
a git submodule, you will have 2.5 choices: 

- You can fork the PyGramm repo, and then build your own PyPi 
  package.  Building the PyPi project is an annoying distraction, 
  but this is the simplest approach if you want to minimize fiddling 
  with the source code of PyGramm.

    - Are you making changes or extensions that could be useful to 
      others?  Great!  Start with approach 1 for your testing
     (maybe using the test version of PyPi), but 
      when you're happy with it, let us know and let's consider folding
      it back into the main PyGramm repository and project.

- You can clone the repo, then move it into your project in 
     source form and make your changes there.  This is likely to 
     require you to extensively modify "import" paths, which is why 
     you might as well just make a copy rather than forking it.  
     There is no going back, so you should take this path if and only
     if you plan to make changes that will not be backward compatible
     with existing uses of PyGramm. 



## Repackaging notes late 2023


### Goals

- Easy installation in virtual environment using PIP
- Easy, reliable test before pushing new version
	- Can evolve out-of-sync with TreeLine, SlackLine
- Compatible with a fairly standard GIT repository structure
	- Subdirectories for source, tests
- Basic project hygiene
	- Relative paths only.  No absolute paths anywhere.

### Reference documents

[Pytest import path handling](
   https://docs.pytest.org/en/7.4.x/explanation/pythonpath.html#pythonpath)
   Importing in Python is a mess.  Pytest seems to do reasonable things to accommodate common ways of packaging tests in subdirectories, for a couple common organizations.  The second paragraph is consistent with my experience that it is very hacky:  “Importing files in Python (at least until recently) is a non-trivial processes, often requiring changing sys.path.”  Now I would hope to learn what “at least until recently” means.
   
[Project structures supported by PyTest](
https://docs.pytest.org/en/7.4.x/explanation/goodpractices.html#test-discovery)  Nominally about test discovery, but more generally applicable to project organization. 

Covers tox, a virtual environment designed to work well with pytest --- it uses virtualenv under the hood but is designed to make it easy to test under multiple virtual environments.  tox in particular has facilities that seem to be designed to test with a locally installed version of a package that acts like the version a user would get when installing a package with pip, although I don’t fully understand that yet.

All these are designed to work together with a .toml file, which is the metadata describing how a library module should be packaged up for publishing in pypi.   I think I’m starting to understand how these work together, but not entirely yet … I think part of the story is that the .toml file can build a local version of what would go in PyPi, and that is what I should be testing against if I want my local tests to reflect what a user of the PyPi package would experience.

Probably beyond what we will use: devpi for managing the deployment process.  The attractive feature of devpi (as I understand it so far) is that it can create a private local index like PyPi, which might be more convenient than testing with the public test version of PyPi.   It is not clear to me yet whether adding this to the stew is worthwhile.

### How Lark does it

I'm following the Lark parser generator as a model because it is reasonably modern (uses current packaging approaches rather than outdated mechanisms) and doesn't look outrageously hacky.  (I also looked at gpxpy, which uses older mechanisms.) 

Lark uses a .toml file, the current recommended way and the way I give manifest information for pygramm.   It is also structured with lark/lark, rather than lark/src/lark.  

The `__init__.py` in lark/lark/init.py is empty, unlike gpxpy, and like I have seen in documentation.  

There is a subdirectory lark/tests, and the `__main__.py` (again with double underscore) imports absolute_import (from future import absolute_import), but I’m not sure why.  It has `from lark import logger` (how does it find lark from a sibling directory?) and `from .test_grammar import TestGrammar` (which look like relative imports to me).  I think `pytest` is manipulating paths to make these work. 

