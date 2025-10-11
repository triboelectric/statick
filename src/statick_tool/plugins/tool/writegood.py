"""Apply writegood tool and gather results.

Website: https://github.com/btford/write-good
"""

import logging
import re
import subprocess
from typing import Match, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class WriteGoodToolPlugin(ToolPlugin):
    """Apply writegood tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "writegood"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return ["md_src", "rst_src"]

    def get_binary(
        self, level: str | None = None, package: Package | None = None
    ) -> str:
        """Get tool binary name.

        Args:
            level: The level to process (optional).
            package: The package to process (optional).

        Returns:
            Name of the tool binary.
        """
        return "write-good"

    # pylint: disable=too-many-locals
    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> list[str] | None:
        """Run tool and gather output.

        Args:
            package: The package to process.
            level: The level to process.
            files: List of files to process.
            user_flags: List of user flags.

        Returns:
            List of output strings or None.
        """
        tool_bin = self.get_binary()

        flags: list[str] = ["--parse"]
        flags += user_flags

        total_output: list[str] = []

        try:
            exe = [tool_bin] + flags + files
            output = subprocess.check_output(
                exe, stderr=subprocess.STDOUT, universal_newlines=True
            )
            total_output.append(output)

        except subprocess.CalledProcessError as ex:
            if ex.returncode in (
                0,
                255,
            ):  # writegood returns 0 or 255 upon linting errors
                total_output.append(ex.output)
            else:
                logging.warning("%s failed! Returncode = %d", tool_bin, ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
            return None

        for output in total_output:
            logging.debug("%s", output)

        return total_output

    def parse_output(
        self, total_output: list[str], package: Package | None = None
    ) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            total_output: List of output strings.
            package: The package to process (optional).

        Returns:
            List of issues.
        """
        writegood_re = r"(.+):(\d+):(\d+):(.+)"
        parse: Pattern[str] = re.compile(writegood_re)
        issues: list[Issue] = []

        for output in total_output:
            for line in output.splitlines():
                match: Match[str] | None = parse.match(line)
                if match:
                    issues.append(
                        Issue(
                            match.group(1),
                            int(match.group(2)),
                            self.get_name(),
                            "suggestion",
                            1,
                            match.group(4),
                            None,
                        )
                    )

        return issues
