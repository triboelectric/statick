"""Apply pycodestyle tool and gather results."""

import logging
import re
import subprocess
from typing import Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class PycodestyleToolPlugin(ToolPlugin):
    """Apply pycodestyle tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            The name of the tool.
        """
        return "pycodestyle"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            A list of file types.
        """
        return ["python_src"]

    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> Optional[list[str]]:
        """Run tool and gather output.

        Args:
            package: The package to scan.
            level: The level of the scan.
            files: The files to scan.
            user_flags: The user flags to pass to the tool.

        Returns:
            The output from the tool.
        """
        flags = ["--format=pylint"]
        flags += user_flags

        total_output: list[str] = []

        tool_bin = self.get_binary()
        try:
            subproc_args = [tool_bin] + flags + files
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )

        except subprocess.CalledProcessError as ex:
            # Return code 1 just means "found problems"
            if ex.returncode != 1:
                logging.warning("Problem %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

            output = ex.output

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
            return None

        total_output.append(output)

        logging.debug("%s", total_output)

        return total_output

    def parse_output(
        self, total_output: list[str], package: Optional[Package] = None
    ) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            total_output: The output from the tool.
            package: The package to scan.

        Returns:
            A list of issues parsed from the output.
        """
        tool_re = r"(.+):(\d+):\s\[(.+)\]\s(.+)"
        parse: Pattern[str] = re.compile(tool_re)
        issues: list[Issue] = []

        for output in total_output:
            for line in output.splitlines():
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    if "," in match.group(3):
                        parts = match.group(3).split(",")
                        if parts[1].strip() == "":
                            issues.append(
                                Issue(
                                    match.group(1),
                                    int(match.group(2)),
                                    self.get_name(),
                                    parts[0],
                                    5,
                                    match.group(4),
                                    None,
                                )
                            )
                        else:
                            issues.append(
                                Issue(
                                    match.group(1),
                                    int(match.group(2)),
                                    self.get_name(),
                                    parts[0],
                                    5,
                                    parts[1].strip() + ": " + match.group(4),
                                    None,
                                )
                            )
                    else:
                        issues.append(
                            Issue(
                                match.group(1),
                                int(match.group(2)),
                                self.get_name(),
                                match.group(3),
                                5,
                                match.group(4),
                                None,
                            )
                        )

        return issues
