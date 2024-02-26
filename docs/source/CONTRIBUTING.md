# 贡献代码

## Contributing Basics / 如何做出贡献？

- Contributing can be as simple as **asking questions**, **[report issues](https://github.com/shepherdpp/qteasy/issues/new?assignees=&labels=&projects=&template=bug-report---bug报告.md&title=)**, **[participating in discussions](https://github.com/shepherdpp/qteasy/discussions)**, **[suggesting new features](https://github.com/shepherdpp/qteasy/issues/new?assignees=&labels=&projects=&template=feature-request---新功能需求.md&title=)**, etc.  **All of these are valuable!**  There are many ways to contribute.  I also very much appreciate when you share the creative things you've done *using* qteasy (both code and plot images).  And, of course, writing code for qteasy is also a great way to contribute.    Thank you.  
  作贡献并不一定意味着添加代码。您可以 **[提出问题](https://github.com/shepherdpp/qteasy/issues/new?assignees=&labels=&projects=&template=bug-report---bug报告.md&title=)**，**[参与讨论](https://github.com/shepherdpp/qteasy/discussions)**，**[提出功能建议](https://github.com/shepherdpp/qteasy/issues/new?assignees=&labels=&projects=&template=feature-request---新功能需求.md&title=)** ，这些都是有价值的贡献。我也非常希望你分享使用`qteasy`创建的交易策略，或实现的好想法。当然，为`qteasy`编写代码也是一种很好的贡献方式。对任何贡献，我在此都深表谢意。

- All of the usual/typical open source contribution guidelines apply (see for example, **[Open Source Guide to Contributing](https://opensource.guide/how-to-contribute/)**).  Therefore, here, on this page, I will mention just a few items that I may be particular about in **qteasy**.  
  您可以参阅所有的开源软件贡献指南（例如，**[开源指南](https://opensource.guide/how-to-contribute/)**）。因此，我仅提到一些我在**qteasy**中可能特别关注的事项。

---
## [Report Issues / 报告问题](https://github.com/shepherdpp/qteasy/issues/new)
- Please provide clear description of the issue and the information of Environment you are working in. Preferably, use [bug report template](https://github.com/shepherdpp/qteasy/issues/new?assignees=&labels=&projects=&template=bug-report---bug报告.md&title=) include following sections in your description:  
  在提交问题报告时，请提供清晰的问题描述和您的工作环境信息。您可以使用[bug提交模板](https://github.com/shepherdpp/qteasy/issues/new?assignees=&labels=&projects=&template=bug-report---bug报告.md&title=)以便在您的描述中包括以下部分：
  - **Your Expectation**: describe what you are trying to achieve while you encountered the issue  
    **你期望看到的结果**：描述你在遇到问题时想要实现的目标或期望看到的结果
  - **Your Method**: provide your code that you think would have given expected results  
    **具体代码**：提供你认为可以得到期望结果的代码
  - **The Outcome**: describe what you actually get with *Your Method*, provide error messages  
    **实际结果**：描述你实际得到的结果，包括错误信息
  - **Your Environment**: Tell me about your machine, OS, and versions of your dependency packages  
    **工作环境**：告诉我你的机器、操作系统和依赖包的版本
  - **Your Configurations**: Print out your qteasy configuration and local datasource overview  
    **系统配置**：打印出你的qteasy配置和本地数据源概览
  - **How to reproduce**: try to provide examples for me to reproduce the issue in order to pin down its root cause  
    **重现方法**：尽量提供可以让我重现问题的例子，以便找出问题的根本原因

---
## Provide Examples and Improve Documents / 提供示例和改进文档
- I highly appreciate if you can provide examples and/or help me with document improvements:  
我尤其希望并感谢您帮助我提供更多的使用示例、或帮助我改进项目文档，例如：
  - Example strategies  
    编写示例交易策略
  - Code snippets  
    分享批处理代码片段
  - Visualizations   
    分享可视化图表
  - Error Corrections   
    纠正文档中的错误
- Please follow below Fork / Clone / Pull Request workflow to provide your contribution to qteasy, I will try to feedback as quickly as possible.   
  请按照下面的Fork/Clone/Pull Request工作流程提供您的贡献，我会尽快给予反馈。

---

## Fork(分支)/Clone(克隆)/Pull Request(合并请求) Workflow / 工作流程
- The standard workflow for contributing on GitHub is called **Fork/Clone**.  For those who may not be familiar, here is a brief summary and some reference links.    
  GitHub上的标准贡献工作流程称为**Fork/Clone (分支/克隆)**。对于那些可能不熟悉的人，这里是一个简要的总结和一些参考链接。
  - *We assume you are familiar with **git** basics: `git clone`, `git commit`, etc*.  
    *我们假设您熟悉git的基础知识：`git clone`、`git commit`等*。
- Note: a "Fork" is just a `git clone` *that is created on, and that lives on, GitHub*.  You create a fork using the **Fork** button on GitHub: This allows GitHub to track the relationship between the original github repository, and your Fork.  
  注意：一个“Fork(分支)”只是一个在GitHub上创建的`git clone`，它保存在GitHub上您自己的账户中。您可以使用GitHub上的**Fork**按钮创建一个Fork：这样GitHub就可以跟踪原始github存储库和您的Fork之间的关系。
- The basic workflow is:  
  基本工作流程如下：
   1. Create a **Fork** of the qteasy repository.  (See references below for details.)  The fork will exist under *your* github account.  
      创建一个**Fork(分支)**，这个分支将存在于*您的*github账户中。
   2. **Clone** *your* Fork to your local machine (`git clone`).  
      将您的Fork分支克隆到本地机器上（`git clone`）。
   3. Work on your cloned copy of the repository, `git commit` the changes, and then **`git push`** them *to your GitHub fork*.  
      修改您本地的代码，用`git commit`提交更改，然后将更改**`git push`**到您的GitHub Fork中。
   4. When you are satisfied with the code in your fork then, **on the GitHub page for your fork, *open a Pull Request (PR)***.  A Pull Request effectively asks for the changes in your fork be pulled into the main qteasy repository.  The PR provides, on github, a place to see the changes, and to post comments and discussion about them.  
      当您对Fork中的代码满意时，**在您的Fork的GitHub页面上，*打开一个Pull Request (PR)***。Pull Request实际上是请求将您Fork中的更改合并到主qteasy存储库中。PR提供了一个地方，可以在GitHub上查看更改，并发布关于它们的评论和讨论。
   5. After code review, if you are asked by a maintainer to make additional changes, you do *not* have to re-enter another Pull Request (as long as the original PR is still open).  Rather, make the changes in your local clone, and simply `git push` them to your fork again.  The changes will automatically flow into the open Pull Request.  
      经过代码审查后，如果维护者要求您进行额外的更改，您不需要重新提交另一个Pull Request（只要原始PR仍然是打开状态）。相反，您可以在本地克隆中进行更改，然后再次`git push`到您的Fork中。更改将自动流入打开的Pull Request中。
   6. When done, the maintainer of the repository will merge the changes from your fork into the qteasy repository.  The PR will automatically be closed.  (Your fork, however, will continue to exist, and can be used again for additional Pull Requests in the future; See GitHub documentation for how to keep your Fork up to date).  
      完成上述步骤后，`qteasy`的维护者将从您的Fork中合并更改到qteasy存储库中。PR将自动关闭。（但是您的Fork将继续存在，并且可以在将来再次用于其他Pull Request；请参阅GitHub文档，了解如何保持您的Fork最新）。

- Some References:
- 一些参考资料：
- GitHub documentation / GitHub文档:
  - **https://docs.github.com/en/get-started/quickstart/contributing-to-projects**
- and some user gists / 一些用户的gists:
  - https://gist.github.com/Chaser324/ce0505fbed06b947d962
  - https://gist.github.com/rjdmoore/ed014fba0ee2c7e75060ccd01b726cb8

---

## Coding Standards / 编码规范
- I am not super strict about adhearing to every aspect of PEP 8, *nor am I lenient*.  I tend to walk the middle of the road: If something is a good and common, then it should be adheared to.   
  我并不非常严格地要求遵守PEP-8的每一条规则，*但也不是完全放任不管*。我倾向于走中间道路：只要是大家普遍遵守的规范和常见的编码习惯，我都可以接受。
- Here are a few items that I tend to care about in particular:  
  以下是我可能会特别关心的一些事项：
  - if you write code, do not use tabs for indentation.  Use 4 spaces.  
    如果您编写代码，请不要使用制表符进行缩进，使用4个空格。
  - If you write code, always provide clear and concise comments explaining what the code is doing.  This is especially important for any code that is not immediately obvious.  
    如果您编写代码，请始终提供清晰简洁的注释，解释代码的作用。这对于功能不太明显的代码尤为重要。
  - If you add a significant feature --that is, a feature for which explaining its usage takes more than just a few sentences-- please also create a "tutorial notebook" for that feature.  **[For examples of tutorial notebooks, please see the jupyter notebooks in the examples folder.](https://github.com/shepherdpp/qteasy/tree/master/examples)**  
    如果您添加了一个重要的功能（即，需要解释其用法的功能不仅仅是几句话），请为该功能创建一个“功能教程”。**[有关功能教程的示例，请参见示例文件夹中的文件](https://github.com/shepherdpp/qteasy/tree/master/examples)**
  - If you add a significant feature, please also create a regression test file **[in the tests folder](https://github.com/shepherdpp/qteasy/tree/master/tests)**, similar to the other regression tests that are there.  *Often, the simplest way to do this is to take a few of the examples from the feature's "tutorial notebook"* (see previous point).  
    如果您添加了一个重要的功能，请在**[tests文件夹](https://github.com/shepherdpp/qteasy/tree/master/tests)**中创建一个回归测试文件，类似于那里的其他回归测试文件。*通常，最简单的方法是从该功能的“功能教程”中选取一些示例*（参见上一点）。
  - If you work on a pre-existing code file, please try to more-or-less emulate the style that already exists in that file.  
    如果您要修改一个已有的代码文件，请尽量模仿该文件中已有的代码风格。
