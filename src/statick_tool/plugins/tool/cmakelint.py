"""Apply cmakelint tool and gather results."""

import logging
import re
import subprocess
from typing import Match, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class CMakelintToolPlugin(ToolPlugin):
    """Apply cmakelint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "cmakelint"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            A list of file types.
        """
        return ["cmake_src"]

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

        output = ""
        cmake_files = []
        if "cmake_src" in package:
            for cmake_file in package["cmake_src"]:
                cmake_files.append(cmake_file)

        tool_bin = self.get_binary()
        try:
            subproc_args = [tool_bin] + flags + cmake_files
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )
        except subprocess.CalledProcessError as ex:
            if ex.returncode == 1:
                output = ex.output
            else:
                logging.warning("Problem %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find cmakelint executable! (%s)", ex)
            return None

        logging.debug("%s", output)
        return output.splitlines()

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
        cmakelint_re = r"(.+):(\d+):\s(.+)\s\[(.+)\]"
        parse: Pattern[str] = re.compile(cmakelint_re)
        issues: list[Issue] = []

        for line in total_output:
            match: Match[str] | None = parse.match(line)
            if match:
                issue_type = match.group(4)
                if issue_type == "syntax":
                    level = 5
                else:
                    level = 3
                issues.append(
                    Issue(
                        match.group(1),
                        int(match.group(2)),
                        self.get_name(),
                        match.group(4),
                        level,
                        match.group(3),
                        None,
                    )
                )

        return issues
