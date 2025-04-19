"""Discovery plugin to find CMake-based projects.

From the CMake manual, valid CMake files are named `CMakeLists.txt` and `*.cmake`. This
module will find those files and make them available as part of the package data.


https://cmake.org/cmake/help/latest/manual/cmake-language.7.html

The contents of `CMakeLists.txt` is used to discover make targets and header files
for the current package. That information is made available as part of the package data.
"""

import argparse
import logging
import os
import re
import shutil
import subprocess
from typing import Match, Optional, Pattern, Union

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class CMakeDiscoveryPlugin(DiscoveryPlugin):
    """Discovery plugin to find CMake-based projects."""

    def get_name(self) -> str:
        """Get name of discovery type.

        Returns:
            Name of the discovery type.
        """
        return "cmake"

    @classmethod
    def get_discovery_dependencies(cls) -> list[str]:
        """Get a list of plugins that must run before this one.

        Returns:
            List of plugin names.
        """
        return ["ros"]

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments.

        Args:
            args: Flags for this plugin will be added to these existing arguments.
        """
        args.add_argument(
            "--cmake-flags", dest="cmake_flags", type=str, help="CMake flags"
        )

    def scan(
        self, package: Package, level: str, exceptions: Optional[Exceptions] = None
    ) -> None:
        """Scan package looking for CMake files.

        Args:
            package: The package to scan.
            level: The level of scanning.
            exceptions: Optional exceptions to apply.
        """
        if self.plugin_context is None:
            return

        package["cmake_src"] = []

        self.find_files(package)

        for file_dict in package.files.values():
            # Check for all lower-case file name since that is how they are stored.
            if (
                file_dict["name"].endswith(".cmake")
                or file_dict["name"] == "cmakelists.txt"
            ):
                package["cmake_src"].append(file_dict["path"])

        package["make_targets"] = []
        package["headers"] = []

        if not os.path.isfile(os.path.join(package.path, "CMakeLists.txt")):
            logging.info("  Package is not cmake.")
            return

        package["cmake"] = [os.path.join(package.path, "CMakeLists.txt")]

        cmake_template = self.plugin_context.resources.get_file("CMakeLists.txt.in")
        shutil.copyfile(cmake_template, "CMakeLists.txt")  # type: ignore

        tool_flags: Union[str, None] = self.plugin_context.config.get_tool_config(
            "make", level, "flags", ""
        )

        extra_gcc_flags = ""
        if tool_flags is not None:
            extra_gcc_flags = tool_flags

        subproc_args: list[str] = [
            "cmake",
            ".",
        ]

        # We are keeping default flags for backwards compatibility. Ideally, we would
        # allow arbitrary flags to be set, but we started off by hard-coding these
        # defaults. In an effort to not break existing installations, we have made it
        # so that new CMake flags must explicitly be set in order to override the
        # default flags.
        default_flags: list[str] = [
            "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
            "-DBUILD_GMOCK=ON",
            "-DBUILD_GTEST=OFF",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            "-DCATKIN_ENABLE_TESTING=OFF",
            "-DCATKIN_SKIP_TESTING=ON",
        ]

        if "cmake_flags" in package and package["cmake_flags"]:
            default_flags.append(package["cmake_flags"])

        path_flags: list[str] = [
            "-DINPUT_DIR=" + package.path,
            "-DSTATICK_EXTRA_GCC_FLAGS=" + extra_gcc_flags,
        ]

        cmake_flags: list[str] = []
        if self.plugin_context.args.cmake_flags is not None:
            cmake_flags = self.plugin_context.args.cmake_flags.split(",")

        if cmake_flags:
            subproc_args.extend(cmake_flags)
        else:
            subproc_args.extend(default_flags)
        subproc_args.extend(path_flags)

        try:
            output: str = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )
        except subprocess.CalledProcessError as ex:
            output = ex.output
            logging.warning("Problem running CMake! Returncode = %d", ex.returncode)
            logging.warning("From %s, running %s", os.getcwd(), subproc_args)
            logging.warning("CMake output: %s", ex.output)

        except OSError:
            logging.warning("Couldn't find cmake executable!")
            return

        logging.debug("%s", output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open("cmake.log", "w", encoding="utf8") as fid:
                fid.write(output)

        self.process_output(output, package)

        logging.info("  %d make targets found.", len(package["make_targets"]))
        logging.info("  %d CMake files found.", len(package["cmake_src"]))

    @classmethod
    def process_output(  # pylint: disable=too-many-locals
        cls, output: str, package: Package
    ) -> None:
        """Parse the tool output.

        Args:
            output: The output to parse.
            package: The package to update.
        """
        # pylint: disable=anomalous-backslash-in-string, line-too-long
        cmake_target_re = r"-- TARGET: \[NAME:(.+)\]\[SRC_DIR:(.+)\]\[INCLUDE_DIRS:(.*)\]\[SRC:(.+)\]"  # NOQA: W605 # NOLINT
        target_p: Pattern[str] = re.compile(cmake_target_re)
        cmake_headers_re = r"-- HEADERS: (.+)"
        headers_p: Pattern[str] = re.compile(cmake_headers_re)
        cmake_roslint_re = r"-- ROSLINT: (.+)"
        roslint_p: Pattern[str] = re.compile(cmake_roslint_re)
        # pylint: disable=line-too-long
        cmake_project_re = r"-- PROJECT: \[NAME:(.+)\]\[SRC_DIR:(.+)\]\[BIN_DIR:(.+)\]"  # NOQA: W605 # NOLINT
        project_p: Pattern[str] = re.compile(cmake_project_re)
        # pylint: enable=anomalous-backslash-in-string

        qt_re = r".*build/.*(ui_|moc_|).*\.(h|cxx)"
        qt_p: Pattern[str] = re.compile(qt_re)

        for line in output.splitlines():
            match_target: Optional[Match[str]] = target_p.match(line)
            if match_target:
                name = match_target.group(1)
                src_dir = match_target.group(2)
                include_dirs = match_target.group(3).split(";")
                src = [
                    src
                    for src in match_target.group(4).split(";")
                    if not qt_p.match(src)
                ]
                src = [
                    (
                        src
                        if os.path.isabs(src)  # noqa F812
                        else os.path.join(src_dir, src)
                    )
                    for src in src
                ]  # NOLINT  # noqa F812

                target = {
                    "name": name,
                    "src_dir": src_dir,
                    "include_dirs": include_dirs,
                    "src": src,
                }
                package["make_targets"].append(target)

            match_headers: Optional[Match[str]] = headers_p.match(line)
            if match_headers:
                headers = match_headers.group(1).split(";")
                headers = [header for header in headers if not qt_p.match(header)]
                package["headers"] += headers

            match_lint: Optional[Match[str]] = roslint_p.match(line)
            if match_lint:
                roslint = os.path.normpath(match_lint.group(1))
                cpplint = os.path.join(roslint, "cpplint")
                if os.path.isfile(cpplint):
                    logging.info("  cpplint script from roslint found at %s", cpplint)
                    package["cpplint"] = cpplint
                else:
                    package["cpplint"] = "cpplint"
            else:
                package["cpplint"] = "cpplint"

            match_project: Optional[Match[str]] = project_p.match(line)
            if match_project:
                package["src_dir"] = match_project.group(2)
                package["bin_dir"] = match_project.group(3)
