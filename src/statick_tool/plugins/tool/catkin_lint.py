"""Apply catkin_lint tool and gather results."""

import logging
import os
import re
import subprocess
from typing import Match, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class CatkinLintToolPlugin(ToolPlugin):
    """Apply catkin_lint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "catkin_lint"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            A list of file types.
        """
        return ["catkin"]

    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> list[str] | None:
        """Run tool and gather output.

        Args:
            package: The package to scan.
            level: The level of the scan.
            files: The files to scan.
            user_flags: The user flags to use.

        Returns:
            The output from the tool.
        """
        flags: list[str] = []
        flags += user_flags
        tool_bin = self.get_binary()

        try:
            subproc_args = [tool_bin, package.path] + flags
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )
        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                logging.warning("catkin_lint failed! Returncode = %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find catkin_lint executable! (%s)", ex)
            return None

        logging.debug("%s", output)
        return output.splitlines()

    @classmethod
    def check_for_exceptions_has_file(cls, match: Match[str], package: Package) -> bool:
        """Manual exceptions.

        Args:
            match: The regex match object.
            package: The package to scan.

        Returns:
            True if the match is an exception, False otherwise.
        """
        message = match.group(5)
        norm_path = os.path.normpath(package.path + "/" + match.group(2))
        with open(norm_path, "r", encoding="utf8") as fid:
            line = fid.readlines()[int(match.group(3)) - 1].strip()
        # There are a few cases where this is ok.
        if message == "variable CMAKE_CXX_FLAGS is modified":
            if line == 'set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++0x")':
                return True
            if line == 'set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")':
                return True
        # There are a few cases where this is ok.
        elif message == "variable CMAKE_C_FLAGS is modified":
            if line == 'set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=gnu99")':
                return True

        return False

    @classmethod
    def get_severity(cls, issue_type: str) -> int:
        """Get level for given issue type.

        Args:
            issue_type: The type of the issue.

        Returns:
            The severity level.
        """
        if issue_type == "error":
            return 5
        if issue_type == "warning":
            return 3
        return 1

    def parse_output(
        self, total_output: list[str], package: Package | None = None
    ) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            total_output: The output from the tool.
            package: The package to scan.

        Returns:
            A list of issues found by the tool.
        """
        lint_re = r"(.+):\s(.+)\((\d+)\):\s(.+):\s(.+)"
        lint2_re = r"(.+):\s(.+):\s(.+)"
        parse: Pattern[str] = re.compile(lint_re)
        parse2: Pattern[str] = re.compile(lint2_re)

        issues: list[Issue] = []
        for line in total_output:
            match: Match[str] | None = parse.match(line)
            if match:
                if package is not None and self.check_for_exceptions_has_file(
                    match, package
                ):
                    continue

                if package is not None:
                    norm_path = os.path.normpath(package.path + "/" + match.group(2))
                else:
                    norm_path = os.path.normpath(match.group(2))

                issues.append(
                    Issue(
                        norm_path,
                        int(match.group(3)),
                        self.get_name(),
                        match.group(4),
                        int(self.get_severity(match.group(4))),
                        match.group(5),
                        None,
                    )
                )
            else:
                match2: Match[str] | None = parse2.match(line)

                if match2:
                    if package is not None:
                        norm_path = os.path.normpath(package.path + "/package.xml")
                    else:
                        norm_path = os.path.normpath("package.xml")

                    message = match2.group(3)
                    if message == "missing build_depend on 'rostest'":
                        message = "missing test_depend on 'rostest'"
                    elif message.startswith("unconfigured build_depend on"):
                        message += (
                            " (Make sure you aren't missing "
                            "COMPONENTS in find_package(catkin ...) "
                            "in CMakeLists.txt)"
                        )

                    message += (
                        " (I can't really tell if this applies for "
                        "package.xml or CMakeLists.txt. Make sure to "
                        "check both for this issue)"
                    )

                    issues.append(
                        Issue(
                            norm_path,
                            1,
                            self.get_name(),
                            match2.group(2),
                            self.get_severity(match2.group(2)),
                            message,
                            None,
                        )
                    )
        return issues
