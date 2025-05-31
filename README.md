# Statick

![Unit Tests](https://github.com/triboelectric/statick/workflows/Statick/badge.svg)
[![Test Action](https://github.com/triboelectric/statick/actions/workflows/self-test.yml/badge.svg)](https://github.com/triboelectric/statick/actions/workflows/self-test.yml)
[![Codecov](https://codecov.io/gh/triboelectric/statick/branch/master/graphs/badge.svg)](https://codecov.io/gh/triboelectric/statick/)
[![PyPI version](https://badge.fury.io/py/statick.svg)](https://badge.fury.io/py/statick)
![Python Versions](https://img.shields.io/pypi/pyversions/statick.svg)
![License](https://img.shields.io/pypi/l/statick.svg)
[![Doc](https://readthedocs.org/projects/statick/badge/?version=latest)](https://statick.readthedocs.io/en/latest/?badge=latest)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
![Daily Downloads](https://img.shields.io/pypi/dd/statick.svg)
![Weekly Downloads](https://img.shields.io/pypi/dw/statick.svg)
![Monthly Downloads](https://img.shields.io/pypi/dm/statick.svg)

Statick makes running static analysis and linting tools easier for all your projects.
Each static analysis tool has strengths and weaknesses.
Best practices recommend running multiple tools to get the best results.
Statick has plugins that interface with a large number of static analysis and linting tools,
allowing you to run a single tool to get all the results at once.

Many tools are known for generating a large number of false positives so Statick provides multiple ways to add
exceptions to suppress false positives.
The types of warnings to generate is highly dependent on your specific project, and Statick makes it easy to run each
tool with custom flags to tailor the tools for the issues you care about.
Once the results are ready, Statick provides multiple output formats.
The results can be printed to the screen, or sent to a continuous integration tool like Jenkins.

Statick is a plugin-based tool with an explicit goal to support external, optionally proprietary, tools and reporting mechanisms.

## Table of Contents

- [Statick](#statick)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
    - [Tool Installation](#tool-installation)
    - [Local Development](#local-development)
  - [Basic Usage](#basic-usage)
  - [Concepts](#concepts)
    - [Discovery](#discovery)
    - [Tools](#tools)
    - [Reporting](#reporting)
  - [Basic Configuration](#basic-configuration)
    - [Levels](#levels)
    - [Profiles](#profiles)
    - [Exceptions](#exceptions)
    - [Timings](#timings)
  - [Existing Plugins](#existing-plugins)
    - [Discovery Plugins](#discovery-plugins)
    - [Tool Plugins](#tool-plugins)
    - [Reporting Plugins](#reporting-plugins)
    - [External Plugins](#external-plugins)
  - [Customization](#customization)
    - [User Paths](#user-paths)
    - [Custom Profile](#custom-profile)
    - [Custom Configuration](#custom-configuration)
    - [Custom Cppcheck Configuration](#custom-cppcheck-configuration)
    - [Custom CMake Flags](#custom-cmake-flags)
    - [Custom Clang Format Configuration](#custom-clang-format-configuration)
  - [Custom Plugins](#custom-plugins)
  - [Examples](#examples)
  - [ROS Workspaces](#ros-workspaces)
  - [Releases](#releases)
  - [Troubleshooting](#troubleshooting)
    - [Make Tool Plugin](#make-tool-plugin)
    - [CMake Discovery Plugin](#cmake-discovery-plugin)
  - [Contributing](#contributing)
    - [Tests](#tests)
    - [Mypy](#mypy)
    - [Formatting](#formatting)
  - [Additional Installation](#additional-installation)
    - [NPM Tools](#npm-tools)
    - [Planning Plugins](#planning-plugins)
  - [Original Author](#original-author)

## Installation

Statick requires Python 3 to run, but can be used to analyze Python 2 projects, among many other languages.

The recommended install method is to create a Python virtual environment and install there.
You can use `venv` or `uv`.

Getting the Python `venv` tool is operating system-specific.
On Ubuntu Linux use `sudo apt-get install python3-venv`.
Activating a Python virtual environment is also operating system-specific.
The example command below is for Linux systems, but it will be similar for other operating systems.

```shell
python3 -m venv .venv
. .venv/bin/activate
pip install statick
```

To use `uv`, follow the [installation instructions](https://docs.astral.sh/uv/).
Create the virtual environment.

```shell
uv venv
. .venv/bin/activate
pip install statick
```

### Tool Installation

You will also need to install any tools you want to use.
Some tools are installed with Statick if you install via pip.
Other tools can be installed using a method supported by your operating system.
For example, on Ubuntu Linux if you want to use the `clang-tidy` _tool_ plugin you can install the tool with apt.

```shell
sudo apt-get install clang-tidy
```

### Local Development

For local development you can clone this repository, activate the virtual environment, then do a local install.
We recommend the virtual environment be outside the Statick directory so that searching through files can skip a large
number of files.

```shell
mkdir -p ~/src/statick
cd ~/src/statick
uv venv
. .venv/bin/activate
git clone <forked repository>
cd statick
uv pip install -e .[docs,test]
```

## Basic Usage

```shell
statick <path of package> --output-directory <output path>
```

This will run the default _level_ and print the results to the console.

To see more detailed output use the `--log` argument.
Valid levels are: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
Specifying the log level is case-insensitive (both upper-case and lower-case are allowed).
See the [logging][logging] module documentation for more details.

## Concepts

Early Statick development and use was targeted towards [Robot Operating System](https://www.ros.org/) (ROS),
with results to be displayed on Jenkins.
Both ROS and Jenkins have a concept of software components as _packages_.
The standard `statick` command treats the _package_ path as a single package.
Statick will explicitly look for ROS packages and treat each of them as an individual unit when running `statick -ws`.

At the same time Statick is ROS agnostic and can be used against many different programming languages.
The term _package_ is still used to designate a directory with source code.

When Statick is invoked there are three major steps involved:

- _Discover_ source code files in each _package_ and determine what programming language the files are written in.
- Run all configured _tools_ against source files that the individual _tool_ can analyze to find issues.
- _Report_ the results.

The default behavior for Statick is to return an exit code of success unless Statick has an internal error.
It can be useful to have Statick return an exit code indicating an error if any issues are found.
That behavior can be enabled by passing in the `--check` flag.
For example, if you are running Statick as part of a continuous integration pipeline and you want the job to fail on
any Statick warnings you can do that by using the `--check` flag.

### Discovery

_Discovery_ plugins search through the package path to determine if each file is of a specific type.
The type of each file is determined by the file extension and, if the operating system supports it, the output of the
`file` command.

### Tools

_Tool_ plugins are the interface between a static analysis or linting tool and Statick.
Each _tool_ plugin provides the types of files it can analyze, then the output of the _discovery_ plugins is used to
determine the specific files that should be analyzed by each tool.

The _tool_ plugin can also specify any other tools that are required to run before the current tool can act.

The _tool_ plugin then scans each package by invoking the binary associated with the tool.
The output of the scan is parsed to generate the list of issues discovered by Statick.

### Reporting

_Reporting_ plugins output the issues found by the _tool_ plugins.
The output can be printed to console (`stdout`) or be used as input to a separate tool or service
that performs additional parsing and processing.

## Basic Configuration

### Levels

Statick has _levels_ of configuration to support testing each _package_ in the desired manner.
_Levels_ are defined in the `config.yaml` file.
Some projects only care about static analysis at a minimal level and do not care about linting for style at all.
Other projects want all the bells and whistles that static analysis and linting have to offer.
That's okay with Statick -- just make a _level_ to match your project needs.

Each _level_ specifies which plugins to run, and which flags to use for each plugin.
If your project only has Python files then your _level_ only needs to run the Python _discovery_ plugin.
If you only want to run _tool_ plugins for _pylint_ and _pyflakes_, a _level_ is how you configure Statick to look for
issues using only those tools.
If you are not using Jenkins then you can specify that you only want the _reporting_ plugin to run that prints issues
to a console.

Each _level_ can be stand-alone or it can _inherit_ from a separate _level_.
This allows users to gradually build up _levels_ to apply to various packages.
All _packages_ can start by being required to pass a _threshold_ _level_.
An _objective_ _level_ can build on the _threshold_ _level_ with more tools or more strict flags for each tool.
A gradual transition of packages from _threshold_ to _objective_ can be undertaken.
Flags from the inherited _level_ can be overridden by listing the same tool under the _level's_ `tools` key with a new
set of flags.

In the following `config.yaml` example the `objective` _level_ inherits from and modifies the `threshold` _level_.
The `pylint` flags from `threshold` are completely modified by the `objective` _level_, and the `clang-tidy` _tool_ is
new for the `objective` _level_.

```yaml
levels:
  threshold:
    tool:
      pylint:
        flags: "--disable=R,I,C0302,W0141,W0142,W0511,W0703
                --max-line-length=100
                --good-names=f,x,y,z,t,dx,dy,dz,dt,i,j,k,ex,Run,_
                --dummy-variables-rgx='(_+[a-zA-Z0-9]*?$$)|dummy*'"
      make:
        flags: "-Wall -Wextra -Wuninitialized -Woverloaded-virtual -Wnon-virtual-dtor -Wold-style-cast
                -Wno-unused-variable -Wno-unused-but-set-variable -Wno-unused-parameter"
      catkin_lint:
        flags: "-W2 --ignore DESCRIPTION_BOILERPLATE,DESCRIPTION_MEANINGLESS,GLOBAL_VAR_COLLISION,LINK_DIRECTORY,LITERAL_PROJECT_NAME,TARGET_NAME_COLLISION"
      cppcheck:
        flags: "-j 4 --suppress=unreadVariable --suppress=unusedPrivateFunction --suppress=unusedStructMember
                --enable=warning,style --config-exclude=/usr --template='[{file}:{line}]: ({severity} {id}) {message}'"
      cpplint:
        # These flags must remain on one line to not break the flag parsing
        flags: "--filter=-build/header_guard,-build/include,-build/include_order,-build/c++11,-readability/function,-readability/streams,-readability/todo,-readability/namespace,-readability/multiline_comment,-readability/fn_size,-readability/alt_tokens,-readability/braces,-readability/inheritance,-runtime/indentation_namespace,-runtime/int,-runtime/threadsafe_fn,-runtime/references,-runtime/array,-whitespace,-legal"
    reporting:
      json:
        files: "true"

  objective:
    inherits_from:
      - "threshold"
    tool:
      pylint:
        flags: "--disable=I0011,W0141,W0142,W0511
                --max-line-length=100
                --good-names=f,x,y,z,t,dx,dy,dz,dt,i,j,k,ex,Run,_
                --dummy-variables-rgx='(_+[a-zA-Z0-9]*?$$)|dummy*'"
      clang-tidy:
        # These flags must remain on one line to not break the flag parsing
        # cert-err58-cpp gives unwanted error for pluginlib code
        flags: "-checks='*,-cert-err58-cpp,-cert-err60-cpp,-clang-analyzer-deadcode.DeadStores,-clang-analyzer-alpha.deadcode.UnreachableCode,-clang-analyzer-optin.performance.Padding,-cppcoreguidelines-*,-google-readability-namespace-comments,-google-runtime-int,-llvm-include-order,-llvm-namespace-comment,-modernize-*,-misc-unused-parameters,-readability-else-after-return'"
      xmllint:
        flags: ""
      yamllint:
        flags: "-d '{extends: default,
                     rules: {
                       colons: {max-spaces-before: 0, max-spaces-after: -1},
                       commas: disable,
                       document-start: disable,
                       line-length: disable}}'"
      cmakelint:
        flags: "--spaces=2 --filter=-linelength,-whitespace/indent"
    reporting:
      json:
        files: "true"
```

Statick supports the use of some multi-line yaml syntax, namely the `>` syntax.
See [Stack Overflow](https://stackoverflow.com/questions/3790454/how-do-i-break-a-string-in-yaml-over-multiple-lines)
and the unit tests for the `config` module for examples.

### Profiles

_Profiles_ govern how each package will be analyzed by mapping _packages_ to _levels_.
A default _level_ is specified, then any packages that should be run at a non-default _level_ can be listed.

Multiple profiles can exist, and you can specify which one to use with the `--profile` argument.
For example, you can have a `profile_objective.yaml` with stricter levels to run for packages.
Pass this profile to Statick.

```yaml
default: threshold

packages:
  my_package: objective

  my_really_good_package: ultimate
```

The `default` key lists the _level_ to run if no specific _level_ listed for a package.

The `packages` key lists _packages_ and override levels to run for those packages.

With the built-in configuration files the default _profile_ uses `default` as the default _level_.
This _level_ runs all available _discovery_ plugins, sets all available _tools_ to use their default flags,
and only runs the _print_to_console_ reporting plugin (which outputs results to the terminal).

With the built-in configuration files another useful _profile_ uses the `sei_cert` _level_.
This _level_ sets all available _tools_ to use flags that find issues listed in
Carnegie Mellon University Software Engineering Institute
"CERT C++ Coding Standard: Rules for Developing Safe, Reliable, and Secure Systems".
The rules and flags can be found in the
[SEI CERT C++ Analyzers](https://wiki.sei.cmu.edu/confluence/display/cplusplus/CC.+Analyzers)
and in the [SEI CERT C Analyzers](https://wiki.sei.cmu.edu/confluence/display/c/EE.+Analyzers) chapters.
The rules in those chapters are updated periodically.
To update Statick support find the relevant tool in the linked chapters and add it to the matching tool configuration
in [`pluggin_mapping`](./src/statick_tool/rsc/plugin_mapping/).

Using the `--level` flag when running Statick will result in that specific level running for all packages regardless
of what the `--profile` is set to.
The specified _level_ from the `--level` flag must exist in the default configuration file or a custom configuration file.

### Exceptions

_Exceptions_ are used to ignore false positive warnings or warnings that will not be corrected.
This is a very important part of Statick, as many _tools_ are notorious for generating false positive warnings,
and sometimes source code in a project is not allowed to be modified for various reasons.
Statick allows _exceptions_ to be specified in three different ways:

- Placing a comment with `NOLINT` on the line of source code generating the warning.
- Using individual _tool_ methods for ignoring warnings (such as adding `# pylint: disable=<warning>`in Python source code).
- Via an `excpetions.yaml` file.

```yaml
global:
  exceptions:
    file:
      # System headers
      - tools: all
        globs: ["/usr/*"]
      # Auto-generated headers
      - tools: all
        globs: ["*/devel/include/*"]
    message_regex:
      # This is triggered by std::isnan for some reason
      - tools: [clang-tidy]
        regex: "implicit cast 'typename __gnu_cxx.*__type' -> bool"

packages:
  my_package:
    exceptions:
      message_regex:
        - tools: [clang-tidy]
          regex: "header guard does not follow preferred style"
      file:
        - tools: [cppcheck, clang-tidy]
        - globs: ["include/my_package/some_header.h"]

ignore_packages:
  - some_third_party_package
  - some_other_third_party_package
```

There are two types of exceptions that can be used in `exceptions.yaml`.

`file` exceptions ignore all warnings generated by a pattern of files.
The `tools` key can either be `all` to suppress warnings from all tools or a list of specific tools.
The `globs` key is a list of globs of files to ignore.
The glob could also be a specific filename.
For an _exception_ to be applied to a specific issue, it is required that the issue contain an absolute path to the filename.
The path for the issue is set in the _tool_ plugin that generates the issues.

`message_regex` exceptions ignore warnings based on a regular expression match against an error message.
The `tools` key can either be `all` to suppress warnings from all tools or a list of specific tools.
The `regex` key is a regular expression to match against messages.
The `globs` key is a list of globs of files to ignore.
The glob could also be a specific filename.
Information about the regex syntax used by Python can be found on the
[Python regex site](https://docs.python.org/2/library/re.html).
The site <https://regex101.com/> can be very helpful when trying to generate regular expressions to match the warnings
you are trying to create an _exception_ for.

_Exceptions_ can either be global or package specific.
To make them global, place them under a key named `global` at the root of the yaml file.
To make them package specific, place them in a key named after the package under a key named `packages` at the root
level of the yaml.

The `ignore_packages` key is a list of package names that should be skipped when running Statick.

### Timings

Use of the `--timings` flag will print timing information to the console.
The information is provided for file discovery, for each individual plugin, and for overall duration.
Example output is

```shell
$ statick . --output-directory /tmp/x --timings

+---------+------------------+-------------+----------+
| package |       name       | plugin_type | duration |
+---------+------------------+-------------+----------+
| statick |    find files    |  Discovery  |  6.7783  |
| statick |       ros        |  Discovery  |  0.0001  |
| statick |      cmake       |  Discovery  |  0.0006  |
| statick |       yaml       |  Discovery  |  0.0034  |
| statick |       java       |  Discovery  |  0.0007  |
| statick |        C         |  Discovery  |  0.0023  |
| statick |      shell       |  Discovery  |  0.0016  |
| statick |      groovy      |  Discovery  |  0.0006  |
| statick |       perl       |  Discovery  |  0.0004  |
| statick |       xml        |  Discovery  |  0.0006  |
| statick |      python      |  Discovery  |  0.0020  |
| statick |      maven       |  Discovery  |  0.0092  |
| statick |    perlcritic    |    Tool     |  0.0000  |
| statick |     cpplint      |    Tool     |  0.0000  |
| statick |       make       |    Tool     |  0.0000  |
| statick |    clang-tidy    |    Tool     |  0.0000  |
| statick |      bandit      |    Tool     |  0.7980  |
| statick |    groovylint    |    Tool     |  3.0717  |
| statick |     pyflakes     |    Tool     |  4.3773  |
| statick |   clang-format   |    Tool     |  0.0063  |
| statick |   pycodestyle    |    Tool     |  2.5456  |
| statick |      black       |    Tool     |  5.0089  |
| statick |      lizard      |    Tool     |  0.6869  |
| statick |       cccc       |    Tool     |  0.0000  |
| statick |     cppcheck     |    Tool     |  0.0163  |
| statick |     xmllint      |    Tool     |  0.0050  |
| statick |      pylint      |    Tool     | 55.3768  |
| statick |   catkin_lint    |    Tool     |  0.0000  |
| statick |    shellcheck    |    Tool     |  0.0736  |
| statick |     yamllint     |    Tool     |  2.2244  |
| statick |    do_nothing    |    Tool     |  0.0000  |
| statick |     spotbugs     |    Tool     |  0.0002  |
| statick |      isort       |    Tool     |  3.6416  |
| statick |    flawfinder    |    Tool     |  0.0000  |
| statick |       mypy       |    Tool     |  0.0022  |
| statick |    uncrustify    |    Tool     |  0.0001  |
| statick |    pydocstyle    |    Tool     |  4.8751  |
| statick |    cmakelint     |    Tool     |  0.0249  |
| statick |   docformatter   |    Tool     |  0.0020  |
| statick | print_to_console |  Reporting  |  0.0318  |
| Overall |                  |             | 89.6734  |
+---------+------------------+-------------+----------+
```

## Existing Plugins

### Discovery Plugins

Note that if a file exists without the extension listed it can still be discovered if the `file` command identifies it
as a specific file type.
This type of discovery must be supported by the discovery plugin and only works on operating systems where the `file`
command exists.

File Type        | Extensions
:--------------- | :---------
C                | `.c`, `.cc`, `.cpp`, `.cxx`, `.h`, `.hxx`, `.hpp`
CMake            | `CMakeLists.txt`, `.cmake`
Maven            | `pom.xml`
PDDL             | `.pddl`
Perl             | `.pl`
Python           | `.py`
ROS              | `CMakeLists.txt` and `package.xml`
Shell            | `.sh`, `.bash`, `.zsh`, `.csh`, `.ksh`, `.dash`
TeX              | `.tex`, `.bib`
XML              | `.xml`, `.launch`
Yaml             | `.yaml`
catkin           | `CMakeLists.txt` and `package.xml`
css              | `.css`
dockerfile       | `Dockerfile*`
groovy           | `.groovy`, `.gradle`, `Jenkinsfile*`
html             | `.html`
java             | `.class`, `.java`
javascript       | `.js`
markdown         | `.md`
reStructuredText | `.rst`

The `.launch` extension is mapped to XML files due to use with ROS launch files.

### Tool Plugins

Tool                               | About
:--------------------------------- | :----
[bandit][bandit]                   | Bandit is a tool designed to find common security issues in Python code.
[black][black]                     | The uncompromising Python code formatter
[catkin_lint][catkin_lint]         | Check catkin packages for common errors
[cccc][cccc]                       | Source code counter and metrics tool for C++, C, and Java
[chktex]                           | LaTeX semantic checker.
[clang-format][clang-format]       | Format C/C++/Java/JavaScript/Objective-C/Protobuf/C# code.
[clang-tidy][clang-tidy]           | Provide an extensible framework for diagnosing and fixing typical programming errors.
[cmakelint][cmakelint]             | The cmake-lint program will check your listfiles for style violations, common mistakes, and anti-patterns.
[cppcheck][cppcheck]               | static analysis of C/C++ code
[cpplint][cpplint]                 | Static code checker for C++
[docformatter][docformatter]       | Formats docstrings to follow PEP 257
[dockerfile-lint][dockerfile-lint] | A rule based 'linter' for Dockerfiles.
[dockerfilelint][dockerfilelint]   | A rule based 'linter' for Dockerfiles.
[eslint][eslint]                   | Find and fix problems in your JavaScript code.
[flawfinder][flawfinder]           | Examines C/C++ source code and reports possible security weaknesses ("flaws") sorted by risk level.
[hadolint][hadolint]               | Dockerfile linter, validate inline bash, written in Haskell.
[htmllint][htmllint]               | An unofficial html5 linter and validator.
[jshint][jshint]                   | JSHint is a community-driven tool that detects errors and potential problems in JavaScript code.
[lacheck]                          | Lacheck is a tool for finding common mistakes in LaTeX documents.
[lizard][lizard]                   | A simple code complexity analyser without caring about the C/C++ header files or Java imports, supports most of the popular languages.
[make][make]                       | C++ compiler.
[markdownlint][markdownlint]       | A Node.js style checker and lint tool for Markdown/CommonMark files.
[mypy][mypy]                       | Optional static typing for Python 3 and 2 (PEP 484)
[npm-groovy-lint][npm-groovy-lint] | This package will track groovy errors and correct a part of them.
[perlcritic][perlcritic]           | Critique Perl source code for best-practices.
[pycodestyle][pycodestyle]         | Python style guide checker
[pydocstyle][pydocstyle]           | A static analysis tool for checking compliance with Python docstring conventions.
[pyflakes][pyflakes]               | A simple program which checks Python source files for errors
[pylint][pylint]                   | It's not just a linter that annoys you!
[pyright][pyright]                 | Static Type Checker for Python
[rst-lint][rst-lint]               | Checks syntax of reStructuredText and code blocks nested within it.
[rstcheck][rstcheck]               | Checks syntax of reStructuredText and code blocks nested within it.
[ruff][ruff]                       | An extremely fast Python linter, written in Rust.
[shellcheck][shellcheck]           | A static analysis tool for shell scripts
[spotbugs][spotbugs]               | A tool for static analysis to look for bugs in Java code.
[stylelint][stylelint]             | A mighty, modern linter that helps you avoid errors and enforce conventions in your styles.
[uncrustify][uncrustify]           | Code beautifier
[val-parser]                       | The plan validation system.
[val-validate]                     | The plan validation system.
[write-good]                       | Naive linter for English prose.
[xmllint][xmllint]                 | Lint XML files.
[yamllint][yamllint]               | A linter for YAML files.

### Reporting Plugins

Reporter | About
:--- | :----
[code_climate][code-climate] | Output issues in valid Code Climate JSON (or optionally strictly [Gitlab][gitlab-cc] compatible) to stdout or as a file.<br>Options:<ul><li>files (string): Output issues to a file.</li><li>terminal (string): Output issues to stdout.</li><li>gitlab (string): Output issues in Gitlab Code Climate format.</li></ul>
do_nothing | Does nothing. Useful when piping output to a separate process and no output is desired. No options.
[json] | Output issues as a JSON list either to stdout or as a file.<br>Options:<ul><li>files (string): Output issues to a file.</li><li>terminal (string): Output issues to stdout.</li></ul>
print_to_console | Print the issues to stdout. This is the default reporting plugin if no _profile_ or _level_ are provided. No options.
[write_jenkins_warnings_ng][jenkins-warnings-ng] | Write Statick results to Jenkins Warnings-NG plugin json-log compatible output. No options. Needs to be used with the `--output-directory` flag.

The intent of all _reporting_ plugins that write files as output is that they will write their output files to the
current directory if no `--output-directory` flag is set.
This should only happen when a _level_ is used that explicitly lists a reporting plugin with file output, in which case
Statick assumes that the user does want the output.

When using the Jenkins _reporting_ plugin, the issues show up formatted and searchable via the
[Jenkins Warnings NG](https://plugins.jenkins.io/warnings-ng/) plugin.
A plot can be added to Jenkins showing the number of Statick warnings over time or per build.
The Statick `--check` flag can be used to cause steps in a Jenkins job to fail if issues are found.
Alternatively, Jenkins can be configured with quality gates to fail if a threshold on the number of issues found is exceeded.

An example [Jenkinsfile](templates/Jenkinsfile) is provided to show how Statick can be used with Jenkins pipelines.

### External Plugins

Known external Statick plugins.
Nearly all of these have been merged into the main repository, but they can serve as examples of how to make custom packages.

Plugin Name      | Repository Location
:--------------- | :-----------------------------------------------
statick-md       | <https://github.com/sscpac/statick-md>
statick-planning | <https://github.com/tdenewiler/statick-planning>
statick-tex      | <https://github.com/tdenewiler/statick-tex>
statick-tooling  | <https://github.com/sscpac/statick-tooling>
statick-web      | <https://github.com/sscpac/statick-web>

## Customization

### User Paths

_User paths_ are passed into Statick with the `--user-paths` flag.
This is where you can place custom plugins or custom configurations.

The basic structure of a user path directory is

```shell
user_path_root
 |- plugins
 |- rsc
```

User-defined plugins are stored in the `plugins` directory.
Configuration files used by the plugins are stored in the `rsc` directory.

It is possible to use a comma-separated chain of _user paths_ with Statick.
Statick will look for plugins and configuration files in the order of the paths passed to it.
Files from paths earlier in the list will override files from paths later in the list.
An example is provided below.

```shell
my_org_config
 |- rsc
     |- config.yaml
     |- exceptions.yaml

my_project_config
 |- rsc
     | - exceptions.yaml
```

To run Statick with this set of configurations, you would do

```shell
statick src/my_pkg --user-paths my_project_config,my_org_config
```

In this example, Statick would use the `config.yaml` from `my_org_config` and the `exceptions.yaml` from `my_project_config`.

### Custom Profile

To run Statick with a custom _profile_ use

```shell
statick src/my_pkg --user-paths my_project_config --profile custom-profile.yaml
```

### Custom Configuration

To run Statick with a custom _configuration_ containing custom _levels_, use `custom-config.yaml` (the filename is
arbitrary) with custom levels defined and `custom-profile.yaml` that calls out the use of the custom _levels_ for your
_packages_.
Custom _levels_ are allowed to override, inherit from, and extend base levels.
A custom _level_ can inherit from a list of base levels.
If you create a _level_ that inherits from a base level of the same name, the new user-defined _level_ will completely
override the base _level_.
This chaining of configuration files is limited to a single custom configuration file.

The filenames used for configurations can be any name you want to use.
If you select `config.yaml` then that will become the base configuration file and none of the levels in the main
Statick package will be available to extend.
This would allow you to include a second custom configuration file on the `--user-paths` path with a name other than
`config.yaml`.

```shell
statick src/my_pkg --user-paths my_project_config --profile custom-profile.yaml --config custom-config.yaml
```

### Custom Cppcheck Configuration

Some _tools_ support the use of a custom version.
This is useful when the type of output changes between _tool_ versions and you want to stick with a single version.
The most common scenario when this happens is when you are analyzing your source code on multiple operating systems,
each of which has a different default version for the _tool_.
_Cppcheck_ is a _tool_ like this.

To install a custom version of _Cppcheck_ you can do the following.

```shell
git clone --branch 1.81 https://github.com/danmar/cppcheck.git
cd cppcheck
make SRCDIR=build CFGDIR=/usr/share/cppcheck/ HAVE_RULES=yes
sudo make install SRCDIR=build CFGDIR=/usr/share/cppcheck/ HAVE_RULES=yes
```

### Custom CMake Flags

The default values for use when running CMake were hard-coded.
We have since added the ability to set arbitrary CMake flags, but left the default values alone for backwards compatibility.
In order to use custom CMake flags you can list them when invoking `statick`.
Due to the likely situation where a leading hyphen will be used in custom CMake flags the syntax is slightly
different than for other flags.
The equals sign and double quotes must be used when specifying `--cmake-flags`.

```shell
statick src/my_pkg --cmake-flags="-DFIRST_FLAG=x,-DSECOND_FLAG=y"
```

### Custom Clang Format Configuration

To use a custom configuration file for `clang-format` you currently have to copy your configuration file into the
home directory.
The reason for this is that `clang-format` does not have any flags that allow for specifying a configuration file.
When `clang-format` is run as part of Statick it ends up using the configuration file in the home directory.

When you have multiple projects it can be fairly easy to use a configuration file that is different from the one meant
for the current package.
Therefore, Statick runs a check to make sure the specified configuration file is the same one that is in the home directory.

In order to actually use a custom configuration file you have to tell Statick to look in a _user path_ that contains
your desired `clang-format` configuration.
You also have to copy that file into your home directory.
The _user path_ is specified with the `--user-paths` flag when running Statick.

```shell
user_path_root
 |- rsc
     |- _clang-format
```

For the file in the home directory, the Statick plugin for `clang-format` will first look for `~/_clang-format`.
If that file does not exist then it will look for `~/.clang-format`.
The resource file (in your _user path_) must be named `_clang-format`.

## Custom Plugins

If you have the need to support any type of _discovery_, _tool_, or _reporting_ plugin that does not come built-in
with Statick then you can write a custom plugin.
Declare the plugin module as a [module entry point] in `pyproject.toml` and provide the path  according to plugin type
(_discovery_, _tool_, _reporting_).

A _user path_ with custom plugins and configuration files may look like

```shell
my-custom-project
  pyproject.toml
  |- src
     |- statick_tool
        |- plugins
           |- discovery
              |- my_discovery_plugin.py
           |- tool
              |- my_tool_plugin.py
              |- my_other_tool_plugin.py
        |- rsc
           |- config.yaml
           |- exceptions.yaml
```

In `pyproject.toml` declare the plugins as entry points.

```toml
[project.entry-points."statick_tool.plugins.discovery"]
my_discovery_name = "statick_tool.plugins.discovery.my_discovery_plugin:MyDiscoveryPlugin"

[project.entry-points."statick_tool.plugins.tool"]
my_tool_name = "statick_tool.plugins.tool.my_tool_plugin:MyToolPlugin"
my_other_tool_name = "statick_tool.plugins.tool.my_other_tool_plugin:MyOtherToolPlugin"
```

For the actual implementation of a plugin, it is recommended to copy a suitable default plugin provided by Statick and
modify as needed.

For the contents of `pyproject.toml`, it is recommended to copy a working external plugin.
An example is [statick-tex].
Those plugins are set up in such a way that they work with Statick when released on PyPI.

## Examples

Examples are provided in the [examples](examples) directory.
You can see how to run Statick against a [ROS package](examples/navigation), a pure [CMake package](examples/sbpl),
and a pure [Python package](examples/werkzeug).

## ROS Workspaces

Statick started by being used to scan [ROS][ros] workspaces for issues.
The `statick -ws` utility provides support for running against a ROS workspace and identifying individual ROS packages
within the workspace.
Each ROS package will then get a unique directory of results in the Statick output directory.
This can be helpful for presenting results using various reporting plugins.

Stand-alone Python packages are also identified as individual packages to scan when using the `-ws` flag.
Statick looks for a `setup.py` or `pyproject.toml` file in a directory to identify Python packages.

For example, suppose you have the following directory layout for the workspace.

- /home/user/ws
  - src
    - python_package1
    - ros_package1
    - ros_package2
    - subdir
      - python_package2
      - ros_package3
      - ros_package4
      - ros_package5
  - build
  - devel

Statick should be run against the workspace source directory.
Note that you can provide relative paths to the source directory.

```shell
statick /home/user/ws/src --output-directory <output directory> -ws
```

Statick can also run against a subset of the source directory in a workspace.

```shell
statick /home/user/ws/src/subdir --output-directory <output directory> -ws
```

## Releases

When it is time to make a new release we like to do it through the GitHub web interface as the release notes end up
looking nicer than creating and pushing a new tag from a local source.

1. Update the `CHANGELOG.md` file to have the new version and release date, and update `statick_tool/__init__.py`
   to have the new version.
   Merge that into `main`.
1. Go to <https://github.com/triboelectric/statick/releases>.
1. Select `Draft a new release`.
1. Select `Choose a tag` and make a new one.
   An example is `v0.9.2`.
   Leave target as `main`.
1. Set `Release title` to the same as the tag, e.g., `v0.9.2`.
1. In the description of `Describe this release` copy in the contents of the `CHANGELOG.md` file.
   Do not use the line from `CHANGELOG.md` with the version number and release date, only the lines after that like
   Added, Fixed, Changed.
   Change the heading emphasis from `###` to `##` for aesthetic purposes.
1. Select `Publish release`.
1. Manually trigger the `Create and publish a Docker image` workflow with the new release tag selected.

After that everything is automated.
A new tag is generated, documentation is updated, packages are published to PyPI (and test PyPI) and Docker images are generated.

## Troubleshooting

### Make Tool Plugin

If you are running Statick against a ROS package and get an error that there is no rule to make target `clean`,
and that the package is not CMake, it usually means that you did not specify a single package.
For example, this is what happens when you tell Statick to analyze a ROS workspace and do not use the `-ws` flag.

```shell
Running cmake discovery plugin...
  Package is not cmake.
cmake discovery plugin done.
.
.
.
Running make tool plugin...
make: *** No rule to make target 'clean'.  Stop.
Make failed! Returncode = 2
Exception output:
make tool plugin failed
```

### CMake Discovery Plugin

If you are running Statick against a ROS package and get an error that no module named `ament_package` can be found,
it usually means that you did not source a ROS environment setup file.

```shell
Running cmake discovery plugin...
  Found cmake package /home/user/src/ws/src/repo/package/CMakeLists.txt
Problem running CMake! Returncode = 1
.
.
.
Traceback (most recent call last):
  File "/opt/ros/foxy/share/ament_cmake_core/cmake/package_templates/templates_2_cmake.py", line 21, in <module>
    from ament_package.templates import get_environment_hook_template_path
ModuleNotFoundError: No module named 'ament_package'
CMake Error at /opt/ros/foxy/share/ament_cmake_core/cmake/ament_cmake_package_templates-extras.cmake:41 (message):
  execute_process(/home/user/.pyenv/shims/python3
  /opt/ros/foxy/share/ament_cmake_core/cmake/package_templates/templates_2_cmake.py
  /home/user/src/ws/statick-output/package-sei_cert/build/ament_cmake_package_templates/templates.cmake)
  returned error code 1
.
.
.
-- Configuring incomplete, errors occurred!
```

## Contributing

### Tests

Statick supports testing through the [tox](https://tox.readthedocs.io/en/latest) framework.
Tox is used to run tests against multiple versions of python and supports running other tools, such as flake8, as part
of the testing process.
To run tox, use the following commands from a git checkout of `statick` (again, with the Python virtual environment activated):

```shell
pip install tox
tox
```

This will run the test suites in Python virtual environments for each Python version.
If your system does not have one of the Python versions listed in `tox.ini`, that version will be skipped.

If running `tox` locally does not work, one thing to try is to remove the auto-generated output directories such as
`output-py27`, `output-py35`, and `.tox`.
There is an included `clean.sh` shell script that helps with removing auto-generated files.

If you write a new feature for Statick or are fixing a bug, you are strongly encouraged to add unit tests for your contribution.
In particular, it is much easier to test whether a bug is fixed (and identify future regressions) if you can add a small
unit test which replicates the bug.

For _tool_ plugins that are not available via pip it is recommended to skip tests that fail when the tool is not installed.

Before submitting a change, please run tox to check that you have not introduced any regressions or violated any code
style guidelines.

Running `tox` for all the tests shows code coverage from unit tests, but the process takes tens of seconds.
When developing unit tests and trying to find out if they pass it can be frustrating to run all of the tests for small
changes.
Instead of `tox` you can use `pytest` directly in order to run only the unit tests in a single file.
If you have a unit test file at `tests/my_module/test_my_module.py` you can easily run all the unit tests in that file
and save yourself a lot of time during development.

```shell
python3 -m pytest --cov=src/statick_tool/ tests/my_module/test_my_module.py
```

To run all the tests and get a report with branch coverage specify the `tests` directory.
Any subdirectory will run all the tests in that subdirectory.

```shell
python3 -m pytest --cov=src/statick_tool/ --cov-report term-missing --cov-report html --cov-branch tests/
```

### Mypy

Statick uses [mypy](http://mypy-lang.org/) to check that type hints are being followed properly.
Type hints are described in [PEP 484](https://www.python.org/dev/peps/pep-0484/) and allow for static typing in Python.
To determine if proper types are being used in Statick the following command will show any errors, and create several
types of reports that can be viewed with a text editor or web browser.

```shell
pip install mypy
mkdir report
mypy --ignore-missing-imports --strict --html-report report/ --txt-report report statick statick_tool/
```

It is hoped that in the future we will generate coverage reports from mypy and use those to check for regressions.

### Formatting

Statick code is formatted using [black][black] and [docformatter][docformatter].
To fix locally use

```shell
pip install black docformatter
black statick statick_tool tests
docformatter -i --wrap-summaries 88 --wrap-descriptions 88 <file>
```

## Additional Installation

### NPM Tools

Make sure you install all the dependencies from npm.
See <https://github.com/nodesource/distributions> for Node/npm installation instructions.

Configure npm to allow a non-root user to install packages.

```shell
npm config set prefix '~/.local/'
```

Make sure `~/.local/bin` exists.
Check your `PATH` with `echo $PATH`.
If `~/.local/bin` is not listed then add it to your `PATH`.

```shell
mkdir -p ~/.local/bin
echo 'export PATH="$HOME/.local/bin/:$PATH"' >> ~/.bashrc
```

Install packages.

```shell
npm install -g dockerfile_lint
npm install -g dockerfilelint
npm install -g markdownlint-cli
npm install -g write-good
```

### Planning Plugins

The [Validate](https://github.com/KCL-Planning/VAL) tool has compilation instructions on their
[Github repository](https://github.com/KCL-Planning/VAL#how-to-compile-val).
The way this tool has been used and tested with Statick is by obtaining the binaries via zip file and putting the
binaries at `/opt/val/`.
The important part is to get the path to the `Validate` binary.
In our typical setup this binary is at `/opt/val/bin/Validate`.
If you have that binary in a different location you will have to update the commands in the rest of this documentation.
An example of where to obtain the zip file is
<https://dev.azure.com/schlumberger/4e6bcb11-cd68-40fe-98a2-e3777bfec0a6/_apis/build/builds/52/artifacts?artifactName=linux64&api-version=6.0&%24format=zip>.

## Original Author

A special note should be made that the original primary author was Mark Tjersland (@Prognarok).
His commits were scrubbed from git history upon the initial public release.

[bandit]: https://github.com/PyCQA/bandit
[black]: https://github.com/psf/black
[catkin_lint]: https://github.com/fkie/catkin_lint
[cccc]: https://github.com/sarnold/cccc
[chktex]: https://www.nongnu.org/chktex/
[clang-format]: https://clang.llvm.org/docs/ClangFormat.html
[clang-tidy]: http://clang.llvm.org/extra/clang-tidy/
[cmakelint]: https://cmake-format.readthedocs.io/en/latest/cmake-lint.html
[code-climate]: https://github.com/codeclimate/platform/blob/master/spec/analyzers/SPEC.md#data-types
[cppcheck]: https://github.com/danmar/cppcheck/
[cpplint]: https://github.com/cpplint/cpplint
[docformatter]: https://github.com/myint/docformatter
[dockerfile-lint]: https://github.com/projectatomic/dockerfile_lint
[dockerfilelint]: https://github.com/replicatedhq/dockerfilelint
[eslint]: https://eslint.org/
[flawfinder]: https://dwheeler.com/flawfinder/
[gitlab-cc]: https://docs.gitlab.com/ee/user/project/merge_requests/code_quality.html#implementing-a-custom-tool
[hadolint]: https://github.com/hadolint/hadolint
[htmllint]: https://github.com/htmllint/htmllint
[jenkins-warnings-ng]: https://plugins.jenkins.io/warnings-ng/
[jshint]: https://jshint.com/about/
[json]: https://www.json.org/json-en.html
[lacheck]: https://ctan.org/pkg/lacheck
[lizard]: https://github.com/terryyin/lizard
[logging]: https://docs.python.org/3/howto/logging.html
[make]: https://gcc.gnu.org/onlinedocs/libstdc++/index.html
[markdownlint]: https://github.com/igorshubovych/markdownlint-cli
[module entry point]: https://setuptools.pypa.io/en/latest/userguide/entry_point.html#entry-points-syntax
[mypy]: https://github.com/python/mypy
[npm-groovy-lint]: https://nvuillam.github.io/npm-groovy-lint/
[perlcritic]: http://perlcritic.com/
[pycodestyle]: https://pycodestyle.pycqa.org/en/latest/
[pydocstyle]: http://www.pydocstyle.org/en/stable/
[pyflakes]: https://github.com/PyCQA/pyflakes
[pylint]: https://pylint.org/
[pyright]: https://github.com/microsoft/pyright
[ros]: https://www.ros.org/
[rst-lint]: https://github.com/twolfson/restructuredtext-lint
[rstcheck]: https://github.com/myint/rstcheck
[ruff]: https://github.com/charliermarsh/ruff
[shellcheck]: https://github.com/koalaman/shellcheck
[spotbugs]: https://github.com/spotbugs/spotbugs
[statick-tex]: https://github.com/tdenewiler/statick-tex
[stylelint]: https://stylelint.io/
[uncrustify]: https://github.com/uncrustify/uncrustify
[val-parser]: https://github.com/KCL-Planning/VAL
[val-validate]: https://github.com/KCL-Planning/VAL
[write-good]: https://github.com/btford/write-good
[xmllint]: http://xmlsoft.org/
[yamllint]: https://yamllint.readthedocs.io/en/stable/
