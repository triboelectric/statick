"""Apply chktex tool and gather results.

Chktex documentation at http://mirrors.rit.edu/CTAN/systems/doc/chktex/ChkTeX.pdf.
"""

import logging
import re
import subprocess
from typing import Match, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ChktexToolPlugin(ToolPlugin):
    """Apply chktex tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "chktex"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            A list of file types.
        """
        return ["tex"]

    # pylint: disable=too-many-locals
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

        total_output: list[str] = []

        tool_bin = self.get_binary()
        try:
            subproc_args: list[str] = [tool_bin] + flags + files
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )

        except subprocess.CalledProcessError as ex:
            # Return code 1 means "found problems".
            # Return code 2 provides correct output with test cases used so far.
            if ex.returncode not in (1, 2):
                logging.warning("Problem %s", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None
            output = ex.output

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
            return None

        logging.debug("%s", output)

        total_output.append(output)

        return total_output

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
        tool_re: str = r"(.+)\s(\d+)\s(.+)\s(.+)\s(.+)\s(\d+):\s(.+)"
        parse: Pattern[str] = re.compile(tool_re)
        issues: list[Issue] = []
        filename: str = ""
        line_number: int = 0
        issue_type: str = ""
        message: str = ""

        for output in total_output:
            for line in output.splitlines():
                match: Match[str] | None = parse.match(line)
                if match:
                    if match.group(1) == "Warning":
                        filename = match.group(4)
                        issue_type = match.group(2)
                        line_number = int(match.group(6))
                        message = match.group(7)
                        issues.append(
                            Issue(
                                filename,
                                line_number,
                                self.get_name(),
                                issue_type,
                                3,
                                message,
                                None,
                            )
                        )

        return issues
