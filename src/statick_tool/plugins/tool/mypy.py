"""Apply mypy tool and gather results."""

import logging
import re
import subprocess
import sys
from typing import Match, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class MypyToolPlugin(ToolPlugin):
    """Apply mypy tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "mypy"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return ["python_src"]

    # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements
    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> list[str] | None:
        """Run tool and gather output.

        Args:
            package: The package to process.
            level: The level to run the tool at.
            files: List of files to process.
            user_flags: List of user flags.

        Returns:
            List of output strings or None.
        """
        flags: list[str] = [
            "--show-absolute-path",
            "--show-error-codes",
            "--no-error-summary",
        ]
        flags += user_flags
        tool_bin = self.get_binary()
        total_output: list[str] = []

        try:
            subproc_args = [tool_bin] + flags + files
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )

        except (IOError, OSError) as ex:
            logging.warning("mypy binary failed: %s", tool_bin)
            logging.warning("Error = %s", ex.strerror)
            return []

        except subprocess.CalledProcessError as ex:
            logging.warning("mypy binary failed: %s.", tool_bin)
            logging.warning("Returncode: %d", ex.returncode)
            logging.warning("%s exception: %s", self.get_name(), ex.output)
            output = ex.output

        total_output.append(output)

        logging.debug("%s", total_output)

        return total_output

    # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements

    def parse_output(
        self, total_output: list[str], package: Package | None = None
    ) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            total_output: List of output strings.
            package: The package being processed.

        Returns:
            List of issues found.
        """
        # file:line: severity: msg type
        tool_re = r"(.+):(\d+):\s(.+):\s(.+)\s(.+)"
        parse: Pattern[str] = re.compile(tool_re)
        issues: list[Issue] = []

        for output in total_output:
            lines = output.splitlines()
            for line in lines:
                if sys.platform != "win32" and not line.startswith("/"):
                    continue
                match: Match[str] | None = parse.match(line)
                if match:
                    issue_type = match.group(5).strip("[]")
                    issues.append(
                        Issue(
                            match.group(1),
                            int(match.group(2)),
                            self.get_name(),
                            issue_type,
                            5,
                            match.group(4),
                            None,
                        )
                    )
        return issues
