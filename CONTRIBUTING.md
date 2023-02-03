## Contributing Basics

- Contributing can be as simple as **asking questions**, **report issues**, participating in discussions, suggesting enhancements, etc.  **All of these are valuable!**  There are many ways to contribute.  I also very much appreciate when you share the creative things you've done *using* qteasy (both code and plot images).  And, of course, writing code for qteasy is also a great way to contribute.    Thank you.

- All of the usual/typical open source contribution guidelines apply (see for example, **[Open Source Guide to Contributing](https://opensource.guide/how-to-contribute/)**).  Therefore, here, on this page, I will mention just a few items that I may be particular about in **qteasy**.

---
## Report Issues
- Please provide clear description of the issue and the information of Environment you are working in. Preferably, include following sections in your description:
  - **Your Expectation**: describe what you are trying to achieve while you encountered the issue
  - **Your Method**: provide your code that you think would have given expected results
  - **The Outcome**: describe what you actually get with *Your Method*, provide error messages
  - **Your Environment**: Tell me about your machine, OS, and versions of your dependency packages
  - **Your Configurations**: Print out your qteasy configuration and local datasource overview
  - **How to reproduce**: try to provide examples for me to reproduce the issue in order to pin down its root cause

---
## Provide Examples and Improve Documents
- I highly appreciate if you can provide examples and/or help me with document improvements:
  - Example strategies
  - Code snippets
  - Visualizations
  - Error Corrections
- Please follow below Fork / Clone / Pull Request workflow to provide your contribution to qteasy, I will try to feedback as quickly as possible.

---

## Fork Clone and Pull Request Workflow
- The standard workflow for contributing on GitHub is called **Fork/Clone**.  For those who may not be familiar, here is a brief summary and some reference links.  
  - *We assume you are familiar with **git** basics: `git clone`, `git commit`, etc*.
- Note: a "Fork" is just a `git clone` *that is created on, and that lives on, GitHub*.  You create a fork using the **Fork** button on GitHub: This allows GitHub to track the relationship between the original github repository, and your Fork.
- The basic workflow is:
  1. Create a **Fork** of the qteasy repository.  (See references below for details.)  The fork will exist under *your* github account.  
  2. **Clone** *your* Fork to your local machine (`git clone`).
  3. Work on your cloned copy of the repository, `git commit` the changes, and then **`git push`** them *to your GitHub fork*.
  4. When you are satisfied with the code in your fork then, **on the GitHub page for your fork, *open a Pull Request (PR)***.  A Pull Request effectively asks for the changes in your fork be pulled into the main qteasy repository.  The PR provides, on github, a place to see the changes, and to post comments and discussion about them.
  5. After code review, if you are asked by a maintainer to make additional changes, you do *not* have to re-enter another Pull Request (as long as the original PR is still open).  Rather, make the changes in your local clone, and simply `git push` them to your fork again.  The changes will automatically flow into the open Pull Request.
  6. When done, the maintainer of the repository will merge the changes from your fork into the qteasy repository.  The PR will automatically be closed.  (Your fork, however, will continue to exist, and can be used again for additional Pull Requests in the future; See GitHub documentation for how to keep your Fork up to date).

- Some References:
- GitHub documentation:
  - **https://docs.github.com/en/get-started/quickstart/contributing-to-projects**
- and some user gists:
  - https://gist.github.com/Chaser324/ce0505fbed06b947d962
  - https://gist.github.com/rjdmoore/ed014fba0ee2c7e75060ccd01b726cb8

---

## Coding Standards
- I am not super strict about adhearing to every aspect of PEP 8, *nor am I lenient*.  I tend to walk the middle of the road: If something is a good and common, then it should be adheared to.  
- Here are a few items that I (perhaps uniquely) tend to care about in particular:
  - If you write code, please don't use tabs; rather use spaces.
  - If you add a significant feature --that is, a feature for which explaining its usage takes more than just a few sentences-- please also create a "tutorial notebook" for that feature.  **[For examples of tutorial notebooks, please see the jupyter notebooks in the examples folder.](https://github.com/shepherdpp/qteasy/tree/examples)**
  - If you add a significant feature, please also create a regression test file **[in the tests folder](https://github.com/shepherdpp/qteasy/tree/tests)**, similar to the other regression tests that are there.  *Often, the simplest way to do this is to take a few of the examples from the feature's "tutorial notebook"* (see previous point).
  - If you work on a pre-existing code file, please try to more-or-less emulate the style that already exists in that file.
