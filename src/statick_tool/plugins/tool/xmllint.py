"""Apply xmllint tool and gather results."""

import logging
import re
import subprocess
from typing import Match, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class XmllintToolPlugin(ToolPlugin):
    """Apply xmllint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "xmllint"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return ["xml"]

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
        flags: list[str] = []
        flags += user_flags
        tool_bin = self.get_binary()

        total_output: list[str] = []

        try:
            subproc_args = [tool_bin] + flags + files
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
            logging.warning("Couldn't find xmllint executable! (%s)", ex)
            return None

        total_output.append(output)

        logging.debug("%s", total_output)

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
        xmllint_re = r"(.+):(\d+):\s(.+)\s:\s(.+)"
        parse: Pattern[str] = re.compile(xmllint_re)
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
                            match.group(3),
                            5,
                            match.group(4),
                            None,
                        )
                    )

        return issues
