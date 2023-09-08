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



  
