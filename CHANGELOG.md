# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Upcoming

The main Statick repository was moved from <https://github.com/sscpac/statick> to
<https://github.com/triboelectric/statick>.

### Added

- Add command line interface arguments to show tool versions. (#490)
  - New arguments to show all tool versions (`--tool-versions-all`) which will not scan anything,
    or just the ones enabled for the current run (`--tool-versions-run`) during a scan.
- Arguments and return description added to all method docstrings.
- Dev container (VS Code) for Statick developers. (#534)
- Support for pyright tool. (#539)
  - Plugin to run tool and parse results.
  - Updates to Statick code to pass pyright.

### Fixed

- Update permissions allowed when publishing Sphinx documentation. (#515)

### Updated

- Docker image now based on Ubuntu 24.04 instead of Ubuntu 20.04.
- Organization name changes relfect repository move. (#535)
- Change types of line number and severity in Issues from string to int. (#529)

### Removed

- Stopped testing on Ubuntu 20.04 runners. (#524)
  - GitHub sent notifications that Ubuntu 20.04 runners will be phased out and completely removed by April 1, 2025.

## v0.12.0 - 2025-02-14

### Added

- All plugins from external repositories owned by NIWC PAC team members were moved into this main repository.
  - Plugins in external repositories are marked as deprecated.

### Fixed

- Found issue with `lizard` output.
  Updated unit test for new output after fix applied upstream.
  - Issue for `lizard` filed at <https://github.com/terryyin/lizard/issues/407>.

### Changed

- Use uv to manage virtual environments and dependencies.
  - Updated CI workflows to use `uv`.
  - Updated README to give options for `uv` and `venv`, with a recommendation for `uv`.

## v0.11.1 - 2025-01-20

API breaking changes introduced.
Pin statick<0.11 if you need the older plugin approach based on yapsy.

### Added

- Use of `pyproject.toml` instead of `setup.py` and `requirements.txt`.
- Added support for Python 3.12 and 3.13.
- Switched from yapsy to setuptools for plugin mechanism. (#508)

### Fixed

- Run `isort` on unit test files.
- Handle updated warning type from `cppcheck` introduced in version 2.8.

## v0.10.0 - 2025-01-03

### Added

- Statick-tex and json-merger included in Statick Docker image. (#506)

### Removed

- Removed support for Python 3.8.

### Fixed

- Updates for new tool versions. (#493)
  - Cpplint unit test updated to match new default warnings from the cpplint 2.0 release.
    - Cpplint 2.0 released on 2024-10-06.
    - <https://github.com/cpplint/cpplint/blob/2.0.0/CHANGELOG.rst#20-2024-10-06>
- Fix command used to run ruff tool.
  - Ruff v0.5.0 requires use of `ruff check` instead of `ruff`.
- Update list of files in clean script to fix shellscript warnings about globs for files with hyphens.
- Ignore new pylint finding for too many positional arguments.
  Finding showed up with pylint 3.3.0.
- Change default value of deep get method to match valid type for reduce function.

## v0.9.5 - 2024-02-29

### Added

- Allow short flag names. (#489, @qdang922)
  - `--output-directory` supports `-o`
  - `--user-paths` supports `-u`
- Add usage examples for reporting plugins to README. (#491, @m0g3ns)
- Install lark as test dependency.
- Process all files at once for groovylint tool plugin. (#493)
  - Similar addition as in v0.9.3.

### Fixed

- Updates for new tool versions. (#493)
  - Latest versions: black (24.1.1), npm-groovy-lint (14.2.0).
  - Fixed unit tests for groovylint tool plugin.
  - Handle parsing issues when CodeNarcServer errors are present.
  - Update source file formatting with latest version of black.

## v0.9.4 - 2023-04-24

### Added

- Unit tests were added to the `exceptions` module with troublesome file to check for `UnicodeDecodeError`. (#478)
- Unit tests were added to the `exceptions` module to check that packages to ignore are parsed correctly from
  exceptions configuration file. (#478)
- Unit tests were added to the `config` module to check that multi-line yaml syntax configurations are successfully
  parsed. (#481)
- Use multi-line yaml for tool flags in default configuration file. (#481)

### Fixed

- Some files cause a `UnicodeDecodeError` exception to be thrown in the `exceptions` module.
  Fixed that bug and now a warning is printed if a file like that is encountered. (#478)
- Fix for Dockerfile smell DL4000. (#482)

### Changed

- Pin version of `docformatter` dependency to be compatible with `black`.
  Update docstrings to match what new version of docformatter expects. (#483)
- Ran `black` and `docformatter` against all the Python test files. (#479)

  ```shell
  cd tests
  find . -name test_\*.py -exec black {} \;
  find . -name test_\*.py -exec docformatter -i --wrap-summaries 88 --wrap-descriptions 88 {} \;
  ```

### Removed

- Drop support for Python 3.7 due to end-of-life on 27 June 2023.
  - See <https://endoflife.date/python>.
- Remove `codecov` package from tox configuration. (#485)

## v0.9.3 - 2023-01-30

Tools that accept a list of files have been sped up considerably.
This is the timing information of running `self_check` level against the main branch and the development branch of
the Statick repository with an AMD 3700x, Ubuntu 20.04, and Python 3.8.
The development branch shows a significant improvement in runtime performance.
The command used was

```shell
./statick . --output-directory /tmp/x --level self_check --log info --timings
```

package | name         | plugin_type | duration (v0.9.2) | duration (unreleased)
------- | ------------ | ----------- | ----------------- | ---------------------
statick | find files   | Discovery   |  9.2810           | 9.3033
statick | black        | Tool        |  4.5896           | 0.1365
statick | docformatter | Tool        |  3.7007           | 0.8105
statick | isort        | Tool        |  4.2516           | 0.1088
statick | mypy         | Tool        |  6.7002           | 1.8145
statick | pydocstyle   | Tool        |  5.2146           | 0.8606
statick | pyflakes     | Tool        |  4.2164           | 0.1893
statick | pylint       | Tool        |  2.2831           | 2.2545
statick | shellcheck   | Tool        |  0.0762           | 0.0352
statick | uncrustify   | Tool        |  0.0001           | 0.0001
statick | xmllint      | Tool        |  0.0039           | 0.0037
statick | yamllint     | Tool        |  1.0534           | 0.1654
Overall |              |             | 41.4780           | 15.8050

Looking at times for Github Actions to run the `self_check` level of Statick shows improvements.

Ubuntu Version | Python Version | v0.9.1 | v0.9.2 | Unreleased
-------------- | -------------- | ------ | ------ | ----------
20.04          | 3.7            | 173    | 97     | 60
20.04          | 3.8            | 187    | 90     | 50
20.04          | 3.9            | 197    | 127    | 51
20.04          | 3.10           | 196    | 84     | 55
20.04          | 3.11           | 159    | 101    | 46
22.04          | 3.7            | 223    | 101    | 52
22.04          | 3.8            | 208    | 95     | 62
22.04          | 3.9            | 186    | 94     | 64
22.04          | 3.10           | 168    | 89     | 40
22.04          | 3.11           | 167    | 79     | 38
mean           |                | 186.4  | 95.7   | 51.8
min            |                | 159    | 79     | 38
max            |                | 223    | 127    | 64

### Added

- Process all source files at once with tools that support passing in a list of files, instead of invoking each tool
  per file. (#470)
- New tool plugin for the [ruff](https://github.com/charliermarsh/ruff) tool.

### Changed

- Change json reporting plugin output file suffix from .json to .statick.json. (#472, #475)
- In GitHub workflow use node action instead of custom node install from source. (#476)

### Fixed

- Using example file in the black test space in unit tests for the black tool plugin. (#470)
- Add missing dependencies to install_requires.
  The docformatter and mypy tools are run by default (if Python files are
  discovered) but they were not included in the package `install_requires`
  list of dependencies.
  Now installing statick in a fresh virtual environment will include and run all
  the available tools. (#465)
- Add check for an empty issue file before trying to read the line for NOLINT.
  Crashes happen if trying to read a line that does not exist. (#467)
- Move flake8 configuration max-line-length option to correct location.
  When running pytest a warning was given about this. The max-line-length
  was being set in the pytest section of our configuration. Moving it to
  the flake8 section fixes the warning and makes more sense logically. (#466, #469)
- In the code climate and json reporting plugins write output files to current directory
  if no output directory is specified. (#471)
- In tex level configuration only use the tex discovery plugin. (#477)

## v0.9.2 - 2022-12-21

The additions to the pylint tool resulted in significant improvements to processing times.

When running the following command:

```shell
statick . --output-directory /tmp/x --profile self_check.yaml --log info --timings --force-tool-list pylint
```

we see these time improvements.
The biggest improvement comes from running pylint once with all Python source files, followed by further improvements
from running with multiple CPU cores.
These results are from a Ryzen 5900x with 24 CPU cores available.

Statick Version | Pylint Timing Info (s)
---------------------- | ------------------------------
main | 40.8708
pylint-multiprocessing with 1 CPU core | 4.6742
pylint-multiprocessing with maximum CPU cores | 2.5462

### Added

- Process all Python source files at once with pylint tool plugin, instead of one pylint run per file. (#460)
- Support [parallel execution](https://docs.pylint.org/run.html#parallel-execution) flag of pylint.
  Set the number of cores used by pylint using the `--max-procs` flag for Statick. (#460)

### Fixed

- Update action versions to get rid of deprecation warnings. (#458)
- Add blank line before URL in docstring for ROS discovery plugin. Fixes warning from new version of docformatter. (#459)

### Removed

- Remove debug print statement when the threshold level is used. (#457)

## v0.9.1 - 2022-12-12

### Added

- Continuous integration tests with Ubuntu 22.04. (#454)
- Continuous integration tests with Python 3.11. (#455)
- Docker image installs Python packages into a Python virtual environment. (#448)

### Changed

- Docker image installs Python tool packages from PyPI instead of apt.
  Uses newer versions of Python tools. (#448)
- Continuous integration uses latest versions of Actions. (#454)

### Fixed

- Groovylint tool plugin specifies flags for host and port to run on loopback device.
  Fixes unit tests in continuous integration. (#454)

### Removed

- Continuous integration tests with Ubuntu 18.04. (#454)

## v0.9.0 - 2022-09-12

### Added

- The new `--level` flag can be set on the command line and will override all other levels, even non-default levels
  specified in a `--profile` flag when running Statick.
  The expectation is that a user setting the `--level` flag will explicitly want that level for the entire Statick run
  (single package or multiple packages in a workspace).
  If separate levels are desired per package then the user should not use the `--level` flag. (#429, #436)
- Ubuntu 22.04 is now included in the main test environment matrix when running GitHub Actions. (#444)
- The `--timings` flag will print timing information to the console after a Statick run.
  Timing information is available for file discovery, for each individual plugin, and for overall duration. (#443)

### Changed

- Default behavior for Statick will now run all available discovery plugins, and run all tool plugins where
  their desired source files are available, then output results only on the terminal.
  The old default behavior was to run the "sei_cert" profile, this is still doable via either of the
  following arguments: `--profile sei_cert.yaml` or `--level sei_cert`. (#432, #435)
- When running unit tests with tox, Statick uses pytest-flake8.
  A recent upstream bug causes issues when using the latest version of pytest-flake8.
  Statick is now pinning the version of pytest-flake8 to the previous major version.
  Details of the upstream issue are at tholo/pytest-flake8#87. (#440)
- Updated configuration files that come with Statick to use the recommended list format when specifying plugins on
  the `inherits_from` setting. (#427)

### Fixed

- CMake discovery plugin and cmakelint tool plugin handle files with .cmake extension. (#434)
  - This follows the CMake manual at <https://cmake.org/cmake/help/latest/manual/cmake-language.7.html#organization>.
    > CMake input files are written in the "CMake Language" in source files named CMakeLists.txt or ending in a
    > .cmake file name extension.
- Support latest PyPI version of mypy.
  Required removing a mypy ignore comment. (#437)
- The ROS discovery plugin was setting the file type of the package to a boolean value rather than a string describing
  the actual file type.
  Mixing types between packages caused bugs in tool plugins.
  The ROS discovery plugin now acts consistently with other discovery plugins. (#439)

### Removed

- Usage of `inherits_from` flag in configuration files as a string is no longer supported.
  The levels specified in `inherits_from` must now be in list format.
  The string usage has been deprecated since v0.7.1. (#427)

## v0.8.1 - 2022-06-06

### Fixed

- Update pylint configurations to not disable bad-continuation.
  Pylint is warning that that option is no longer available.

## v0.8.0 - 2022-05-31

Bugs were fixed in the `cccc` and `isort` tool plugins.
The nature of the bugs in each tool resulted in under-reporting of issues discovered by using the tools.
By fixing the tool plugins it is possible that users may find that more issues are now discovered using
the same tool configurations as before.
If a user does not want to fix the additional warnings yet they can pin the version of Statick to `statick<=0.7`.

### Added

- [Code Climate](https://github.com/codeclimate/platform/blob/master/spec/analyzers/SPEC.md#data-types) reporting plugin.
  This plugin can be used to provide output in GitLab merge requests via the
  [Code Quality](https://docs.gitlab.com/ee/user/project/merge_requests/code_quality.html#implementing-a-custom-tool)
  feature. (#416)
- List of existing reporting plugins to README. (#417)
- Survey of metrics for software quality assurance to docs. (#413)

### Changed

- Update Docker image tag to remove the `v` prefix. (#409)

### Fixed

- Support for user flags passed to the isort tool (#414).
- Collect output of CCCC tool for each file individually instead of using the output from the last file it ran on. (#412)
  NOTE: This change will likely result in more issues being found by this tool.

## v0.7.2 - 2022-03-09

### Fixed

- Add deprecated module to the required install dependencies.
  Fixes crash when running Statick.

## v0.7.1 - 2022-03-08

### Added

- A level can inherit from multiple child levels.
  This makes it easier to tailor levels for specific file types and tools, then combine the targeted levels into a
  more comprehensive level for projects that have heterogeneous file types.

### Fixed

- Ensure file type key is in package information before reading the variable.
  This makes all the tool plugins consistent in how they read in package information.
- Change test workflow to not fail if Codecov upload fails.
  Codecov uploads are not stable and result in false Action failures.

### Deprecated

- When using the `inherits_from` flag for a level the flag should be a list instead of a string.
  This change was made to support levels that can inherit from multiple child levels.
  Support for string `inherits_from` flags will continue through the v0.7 releases.
  The README and unit tests have example of how to specify the `inherits_from` flag as a list.

## v0.7.0 - 2022-01-04

### Removed

- Drop support for Python 3.6 due to end-of-life of that distribution.
  See <https://endoflife.date/python>.
  To continue using Statick with Python 3.6 [pin the version](https://pip.pypa.io/en/stable/user_guide/)
  used to the `0.6` tags.
  An example is at the discussion at <https://github.com/triboelectric/statick/discussions/376>.

## v0.6.3 - 2021-12-14

### Added

- Tests run on Python 3.10.
- Docker image created and published on each new release.
  Image forms the basis of the new Statick Github Action.
  See <https://github.com/triboelectric/statick-action>. (Greg Kogut, @gregtkogut)
- Test workflow runs on a weekly, scheduled timer. (Greg Kogut, @gregtkogut)
- Test workflow can be manually triggered to run. (Greg Kogut, @gregtkogut)
- Stand-alone Python packages are discovered as part of running Statick in workspace mode.
  A Python package is identified as any directory containing a file named `setup.py` or `pyproject.toml`.

### Fixed

- Explicitly specify `encoding` when using the `open` command on files, as recommended by pylint. (Greg Kogut, @gregtkogut)

### Removed

- Skip some unit tests for the clang-tidy tool on Windows.

## v0.6.2 - 2021-06-15

### Added

- Groovy discovery plugin and tests.
- [NPM Groovy Lint](https://nvuillam.github.io/npm-groovy-lint/) tool plugin and tests.

### Fixed

- Install missing library type stubs for PyYAML.
  Needed for mypy to properly identify type hints.

### Removed

## v0.6.1 - 2021-05-27

### Added

- New plugin to run the `isort` tool.
  Use of the `isort` tool has been added to the `self_check` level.
- All print statements where variables are referenced have been converted to `f-strings`.
- All type hints were changed from comment style to inline style.
  The comment style of type hints was required when using Python 3.5.
- The `black` tool was added to the Statick package requirements file.
  The `black` tool is now run for the `self_check` level.
  The tool was not installable with Python 3.5.

### Fixed

- Unit tests that rely on the `file` command to be present are now skipped if the file command does not exist.
  These changes were developed and tested when running the unit tests in PowerShell on Windows 10.
- For testing with Actions, the installed version of Node was upgraded from v10 to v14.
  Node v10 is no longer supported.
  Node v14 is recommended by the developers as it is a long-term support (LTS) release.

### Removed

- Deprecated discovery plugin `catkin` packages has been removed.
  All functionality for discovering `catkin` packages is in the `ros` discovery plugin.
- Deprecated reporting plugin for `print_json` has been removed.
  All functionality for print `json` output is in the `json_reporting_plugin`.

## v0.6.0 - 2021-05-14

### Removed

- Remove testing support for Ubuntu 16.04 and Python 3.5.
  There is no guarantee Statick will work in those environments any longer.

## v0.5.5 - 2021-05-14

This is expected to be the final release that supports Python 3.5.
Ubuntu 16.04 has reached end-of-life status.
The final release of ROS Kinetic has been made.
See <https://github.com/triboelectric/statick/discussions/290> for a discussion on Python 3.5 support in Statick.

### Added

- An alternate installation method that uses git+https has been described in the README.
  This method is useful for local installations and when trying new changes in Docker images.

### Fixed

- After upgrading the black tool there were formatting changes made to a unit test file.
  Those formatting changes were applied.

## v0.5.4 - 2021-03-23

### Added

- Add new reporting plugin that will provide JSON output to the terminal and/or to a file.
  To control the plugin outputs you can add the following to your existing level configuration.

  ```yaml
  levels:
  x:
    discovery:
      discovery_plugin:
    reporting:
      json:
        terminal: "True"
        files: "True"
    tool:
      tool_plugin:
        flags: ""
  ```

### Deprecated

- The `print_json` reporting plugin is marked as deprecated and will be removed in v0.6 series.
  The functionality is completely replaced with the `json` reporting plugin.

## v0.5.3 - 2021-03-04

### Added

- Add option to the `clang-format` tool to report any issues found per line.
  The per line differences are shown in diff format.
  This output is an alternative to the current option of a single issue per file.
  The default is to still output a single issue per file.
  The ability to parse `clang-format` XML output and format in diff style was borrowed from
  [ament_lint](https://github.com/ament/ament_lint), developed mainly by Dirk Thomas (@dirk-thomas).

### Fixed

### Removed

## v0.5.2 - 2021-02-11

### Fixed

- In the Exceptions module, open files in read-only mode when filtering the lines for the NOLINT string.
  Attempting to open files owned by root in read-write mode was causing a `PermissionError` and Statick would crash.

## v0.5.1 - 2021-02-08

### Added

- Allow custom configuration levels to inherit from base levels.
  The base levels are either the ones that are supplied by Statick, or those set in `config.yaml` on a `--user-paths` path.
  The custom configuration levels must be in a file on the `--user-paths` path.
- Automatically creating the output directory if it does not exist. (Alexander Xydes, @xydesa)
- Add a reporting plugin that does nothing.
  This can be helpful when a reporting plugin is required but you do not want any side effects.
  One use case is piping Statick output to a separate process.
- Add documentation on how to use pytest for running a subset of unit tests.
  Shows how to get line coverage and branch coverage metrics.
  This can help speed up Statick developers workflow.

### Fixed

- Batch all log statements inside a statick ws subprocess and only output at the end of the subprocess.
  This groups all console output for a single package together.
  Previously, the output from multiple packages would be interleaved and difficult to read. (Alexander Xydes, @xydesa)
- Only outputting warning about docformatter failing if returncode is not 3, which is used to indicate that files
  would be formatted. (Alexander Xydes, @xydesa)
- Improve the deprecation warning message for the catkin discovery plugin.
  Gives the version number when the plugin will be removed.
- Add documentation on how to use custom configurations for the clang-format tool.
  This used to be institutinal knowledge and the usage was not clear.

## v0.5.0 - 2021-01-14

This release adds some breaking changes to the use of Statick, but all of the old functionality can still be accessed
using the new approaches.

To scan a ROS workspace with multiple packages there used to be a separate executable named `statick_ws`.
That same functionality is now accessed via the main `statick` executable by passing in the `-ws` flag.
Anywhere that you used to use `statick_ws <workspace_directory/src>`, change that to `statick <workspace_directory/src> -ws`.

When scanning a ROS workspace all of the packages in that workspace will now be scanned in parallel.
The default number of packages to scan in parallel is half the number of CPU cores on the current computer.
This was selected as a compromise between running Statick on continuous integration servers and for local developers.
To get back to the previous behavior of scanning a single package at a time, use the flag `--max-procs 1`.
To have Statick figure out the number of available CPU cores and use all of them, use the flag `--max-procs -1`.
To use a specific number of CPU cores (`N`) up to the maximum available, use the flag `--max-procs N`.

Statick switched from raw `print()` statements to using the Python built-in logging module.
Most output is now suppressed by default.
To get back to the previous amount of output verbosity use the flag `--log INFO`.
Previously, the `--show-tool-output` flag was used to add even more verbosity.
That flag will work for the v0.5 releases, but will be removed for v0.6 releases.
Instead you should now use the flag `--log DEBUG`.

### Added

- Allow `statick_ws` to scan packages in parallel using the multiprocess module. (Alexander Xydes, @xydesa)
- Make `statick_ws` a `-ws` flag on the main statick executable instead of a standalone executable. (Alexander Xydes, @xydesa)
- Convert use of print() and show tool output flags to the built-in Python logging module.
- Add support for yml extension to yaml discovery plugin. (Alexander Xydes, @xydesa)
- Apply docformatter to format docstrings. Add that tool to the list to run at the self-check level.
- Add reporting plugin to output issues to the console in JSON format. (Alexander Xydes, @xydesa)

### Fixed

- Add mypy to requirements.txt.
- Remove trailing colon from filename when adding issues for black tool.
- Add parsing of black's internal parse error syntax. (Alexander Xydes, @xydesa)
- Check for a valid plugin context before accessing plugin context variables related to the existence of an output directory.

### Removed

- Remove unused files that are duplicated by CI files that show how to install packages.

## v0.4.11 - 2020-12-22

### Added

- A big speedup improvement of roughly 3x was implemented for the discovery phase.
  The main discovery plugin will now walk through the filesystem once per package and cache information about absolute
  file paths and `file` command output.
  Each discovery plugin can now use that cached information instead of walking the filesystem itself. (Alexander Xydes, @xydesa)
- Any directory with `COLCON_IGNORE` (and all of its subdirectories) will be ignored by `statick_ws`.
  This is a standard file used by ROS2 to indicate that a ROS2 package should be ignored. (Alexander Xydes, @xydesa)

## v0.4.10 - 2020-12-15

### Added

- Add support to ROS discovery plugin for ROS2 Python-only packages that do not contain `CMakeLists.txt`.
  Second attempt that fixed some bugs from first attempt.
- Add section to the `README` about `statick_ws` usage.
- Convert `lizard` tool plugin to use Python API and support user flags. (Jacob Hassold, @jhdcs)

### Fixed

- Remove `~/_clang-format` after each unit test where it is copied to the home directory.
- Fix bug in lizard tool plugin where the directory to scan for files was not set properly.
  Thanks Jacob Hassold (@jhdcs) for finding the bug.
- Ignoring any subdirectories in `statick_ws` if the current directory contains `CATKIN_IGNORE` or `AMENT_IGNORE`.
  (Alexander Xydes, @xydesa)

## v0.4.9 - 2020-12-09

### Fixed

- Reverted changes to ROS discovery plugin to support Python-only packages.
  Those changes were causing crashes for some users.
  We will get those changes back into a future release, but take out the bugs.

## v0.4.8 - 2020-12-09

### Added

- The ROS discovery plugin now supports Python-only packages that do not contain a `CMakeLists.txt` file.
- Improved the output of the cpplint tool plugin.
  When no make targets or C/C++ headers have been discovered the tool no longer gives confusing message about the
  cpplint executable not being found.

## v0.4.7 - 2020-11-25

### Fixed

- Fix bug in CCCC tool plugin where an empty list of source files results in trying to print output before it is available.
  The result of the bug was the Statick tool crashing.
- Fix title underlines in documentation files.
  Based on sphinx linting feedback from ammaraskar/sphinx-action.

## v0.4.6 - 2020-11-18

### Added

Date:   Tue Nov 17 08:17:55 2020 -0800

- Add Python 3.9 support.
  All unit tests and self checks are performed using Python 3.9.
  This required modifying the `self_check` configuration to disable the pylint flag `--unsubscriptable-object` due
  to documented issues with pylint, Python 3.9, and type hints.
- Add new ROS discovery plugin.
- Add feature that allows discovery plugins to depend on other discovery plugins, necessary for getting additional
  CMake flags from ROS discovery plugin to the CMake disocvery plugin.

### Deprecated

- The catkin discovery plugin is now marked as deprecated since the ROS discovery plugin is more general.
  For now both plugins run by default, but the catkin discovery plugin will be removed in a future version.

## v0.4.5 - 2020-11-12

### Added

- Generate and publish Sphinx documentation to GitHub Pages on all new releases.
- Add discovery plugin to find shell files.
- Add tool plugin for [shellcheck](https://www.shellcheck.net/).
- Update documentation to list plugin types and link to tool documentation.

### Fixed

- Fix for running `cmake_discovery_plugin` with some ROS 2 packages that contain messages. (Alexander Xydes, @xydesa)

## v0.4.4 - 2020-10-16

### Fixed

- The `cppcheck` and `cpplint` tool plugins no longer depend on the `make` tool plugin to run first.
  The tool plugins get all of the information they need, such as source files, headers, and include directories,
  from the `cmake` discovery plugin.
  This greatly speeds up Statick runs that use the `cppcheck` and/or `cpplint` tools but do not use the `make` tool.
- Now we are using a configuration file for Codecov so that reports from Windows are reported with the correct path.
  This allows the reports from all operating systems to be merged together, restoring prior behavior.

## v0.4.3 - 2020-10-09

### Added

- Overhaul of documentation.
  README contains more structure and examples by consolidating README and GUIDE.
- Regular expression-based exceptions can now be applied to a subset of files that match a pattern ("glob").
  This feature is available for both global and package exceptions.
- Custom CMake flags can be added to the CMake discovery plugin.
  Those flags will be used by the Make tool plugin.
  The default values have not changed, but can be overridden.
- The clang-format tool can now use either `_clang-format` or `.clang-format` as the configuration file.
  If the `_clang-format` file exists then that is the configuration file that is used.
  Otherwise, Statick will look for `.clang-format`.
  This allows users to keep the configuration file hidden in their home directories.

### Fixed

- Make tool plugin no longer causes Statick to crash if `make_targets` are missing.
- When the Black tool encountered an internal error it would silently fail as far as Statick was concerned.
  Statick is now aware of internal errors from Black and reports the information as an issue.
- The exceptions module can now handle `exceptions.yaml` configuration files that are empty.

## v0.4.2 - 2020-08-12

### Added

- Fallback for cpplint discovery that will use system install if ROS provided version
  is not found.
  Allows cpplint tool to work without ROS and on ROS Noetic, where the roslint package
  changed the names of the cpplint executables.

## v0.4.1 - 2020-08-11

### Added

- Tests performed on Ubuntu 20.04.
- Black formatting applied and enforced.
- Using mypy with `--strict` flag.
- Added lots of unit tests to get to 100% code coverage.

### Fixed

- Bug fixed that caused CMake discovery plugin to fail when using ROS packages on
  Ubuntu 20.04 with ROS Noetic.
- Bug fixed that would cause certain regular expression comparisons to fail.
- Code coverage reports are now more accurate by using multiple operating systems.
- Better handling of loading yaml by adding exceptions. (Alexander Xydes, @xydesa)
- Improved parsing of pyflakes output.

### Removed

- Legacy Jenkins reporting plugin was removed due to the plugin being deprecated upstream.
  Support was already added for the new, recommended Next Generation Jenkins reporting plugin.

## v0.4.0 - 2020-05-01

### Added

- Exit code is now based only on whether internal workings of Statick are successful.
  This is a change from previous versions, where the presence of detected issues would trigger an error code when exiting.
  To have the previous behavior use the newly introduced `--check` argument when running Statick.
  This behavior was standardized between `statick` and `statick_ws`.
- Documentation for new tool plugins (black, docformatter).

### Fixed

- Using more reliable way of installing nodejs on Ubuntu 18.04 in Actions.
  This is needed to install and run markdownlint as part of statick-md.

## v0.3.8 - 2020-04-13

### Added

- New tool plugin for [docformatter](https://github.com/myint/docformatter).
- New troubleshooting section in README.
  - Started with make tool plugin.
- Switched from pep257 in tox to pycodestyle and pydocstyle.
- Switched continuous integration from Travis CI to Github Actions.
- Package is published to PyPI automatically from Actions when new tags are created.

### Fixed

- Improved regular expressions in setup.py for installing resource files.
- Updated parsing in pyflakes tool to handle what seems like new formats for the tool output.
  - Unit tests were added to ensure new output format can be parsed.
  - Previous formats are still parsed properly.
- Using installed `.markdownlintrc` from statick-md instead of using custom one.
  - The statick-md plugin had a new release that installed the configuration file properly.

### Removed

- No longer using `from __future__ import print_function`.
  - This is possible due to the move to Python 3.5+, where Python 2.7 support was dropped.

## v0.3.7 - 2020-03-23

### Added

- Formatted all code using black.
  Added Github Action to ensure future commits are consistent with black formatting.
- Added a tool plugin for [black](https://github.com/psf/black).
- Added a tool plugin for [mypy](http://mypy-lang.org/).

## v0.3.6 - 2020-03-18

### Fixed

- A bug in how type hints were applied caused issues with Python 3.5, which is the
  default on Ubuntu 16.04-based operating systems.
  Switching to comment-style type hints for variables made Statick work with Python 3.5 again.
  Thanks to Greg Kogut (@kogut) for discovering the issue.

## v0.3.5 - 2020-03-18

### Added

- Using type hints as introduced in Python 3.5 and improved in Python 3.6.
  Type hints are described in [PEP 438](https://www.python.org/dev/peps/pep-0483/)
  and [PEP 484](https://www.python.org/dev/peps/pep-0484/).
  They provide static typing for methods and variables.
  The use of mypy is encouraged to look for errors in expected types.
- Using [statick-md](https://github.com/sscpac/statick-md) plugin to check Markdown files.

### Fixed

### Removed

- No longer supporting pypy3 due to issues with type hints and mypy.

## v0.3.4 - 2020-02-26

### Added

- Using fewer CMake targets during build.

### Fixed

- Open issues filename with utf-8 encoding to avoid UnicodeDecodeError exception.
- CMake and Spotbugs plugins no longer write output logs if output directory is not specified.

### Removed

## v0.3.3 - 2020-02-19

### Added

- Github workflows for Actions.
  These are just starting but they may replace Travis CI in the future.
- Made 3.8 the default version for CI testing.

### Fixed

- Added needed `install_requires` entries in setup.py to allow Statick to work out of the box (in the pip sense).
- The `statick_ws` command now supports running without an output directory.
- The xmllint unit tests will be skipped if xmllint executable is not available.
  This can happen when apt dependencies are not going to be installed.

### Removed

- Python 3.5 is no longer supported.
  It is not getting updates any longer, and is not available on Github Actions.

## v0.3.2 - 2020-02-18

### Added

- Ability for Jenkins Warning NG reporting plugin to handle severity as int or string type. (Alexander Xydes, @axydes)

### Fixed

### Removed

## v0.3.1 - 2020-02-06

### Added

- Reporting plugin for the
  [Jenkins Warnings Next Generation](https://wiki.jenkins.io/display/JENKINS/Warnings+Next+Generation+Plugin)
  plugin. (Alexander Xydes, @axydes)
  - Updated Jenkinsfile template to reflect usage of new plugin.
- Renamed file writing reporting plugin to write Jenkins warnings reporting plugin. (Alexander Xydes, @axydes)
- More helpful, explicit error messages from the clang-format tool plugin.

### Fixed

- Not writing log files if no output directory is specified.
- The make tool plugin will now cause Statick to exit with error condition if the tool does not run successfully.

### Removed

## v0.3.0 - 2020-01-31

Note that a breaking change was made to how the output directory is specified for writing results to a file.
The default changed from always writing output files to only writing output files when the `--output-directory`
argument is specified.
The previous way to run Statick was:

```shell
statick my-project statick-output
```

With this update you can run with output files:

```shell
statick my-project --output-directory statick-output
```

or without output files:

```shell
statick my-project
```

### Added

- Skipping integration tests for tool plugins where the tool is not available via pip.
- Statick works better on Ubuntu 18.04. (Greg Kogut, @kogut)

### Fixed

- Clang-format tool now supports multiple language specifications in the configuration file.
  The fix also allowed for increased unit test coverage of the tool. (Alexander Xydes, @xydesa)

### Removed

- Support for Python 2.7, Python 3.4, and pypy.
- Required argument for `output_directory`.
  It is now an optional argument `output-directory` as described above.

## v0.2.15 - 2019-12-26

### Added

- Changed build and deploy Travis stages from Python 2.7 to Python 3.5.
- Unit tests for file dicovery now cover the case where the `file` command is not available.

### Fixed

- Bug found when using tool under Ubuntu 18.04 where the diff calculated for clang-format desired and actual
  configurations would produce empty lines.
  This caused the tool to throw an exception.
  Fixed by checking that there is diff output before trying to read it.
- The uncrustify unit test now works on Ubuntu Bionic.
- Several pylint issues related to unnecessary elif and else after break/continue/raise lines were cleaned up.

### Removed

## v0.2.14 - 2019-11-21

### Added

- Support for Python 3.8 (build and unit tests on Travis).
- Updated unit tests for main Statick module.

### Fixed

- Install patterns updated to prevent picking up the `plugin_mapping` directory multiple times. (Kevin Kredit, @kkredit)
- Handle more varied output from pyflakes tool.

### Removed

- Removed support for previously deprecated pep8 and pep257 tools.
  The pycodestyle and pydocstyle tools provide the same functionality, only the tool name needs to change in the
  configuration file.

## v0.2.13 - 2019-09-22

### Added

- Python 3.8-dev is now part of the test matrix for Travis jobs.

## v0.2.12 - 2019-09-08

### Fixed

- Reverted method used by clang-format tool plugin to obtain output.
  New way worked locally but failed on Travis CI jobs.

## v0.2.11 - 2019-09-08

### Added

- cpplint added to requirements.txt
- Updated and new unit tests for:
  - cpplint tool plugin
  - xmllint tool plugin
  - yamllint tool plugin
  - catkin_lint tool plugin
  - make tool plugin
  - clang-format tool plugin
  - pylint tool plugin
  - lizard tool plugin
  - pyflakes tool plugin
  - cmakelint tool plugin
  - uncrustify tool plugin
  - CCCC tool plugin
  - pycodestyle tool plugin
  - perlcritic tool plugin
  - CMake discovery plugin
  - config module
  - discovery module
  - exceptions module

### Removed

- Gauntlet tool removed due to perceived lack of use in community.

## v0.2.10 - 2019-05-27

### Added

- Improved documentation on how to create third-party plugins that can be released to PyPI.
- Support for custom files for defining configuration and exceptions.

### Fixed

- Added additional error checking prior to opening and reading configuration files.

## v0.2.9 - 2019-04-30

### Added

- Started keeping a Changelog (Chris Reffett, @creffett)
- Configuration support for tex tools (chktex and lacheck plugins in separate repository)

### Fixed

- Fix backtrace when Statick is run with a nonexistent file as a profile (Chris Reffett, @creffett)
