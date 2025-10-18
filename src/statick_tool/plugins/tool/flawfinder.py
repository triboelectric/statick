"""Apply flawfinder tool and gather results."""

import logging
import re
import subprocess
from typing import Match, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class FlawfinderToolPlugin(ToolPlugin):
    """Apply flawfinder tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "flawfinder"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return ["c_src"]

    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> list[str] | None:
        """Run tool and gather output.

        Args:
            package: The package being analyzed.
            level: The analysis level.
            files: List of files to process.
            user_flags: List of user flags.

        Returns:
            List of output strings or None.
        """
        flags: list[str] = ["--quiet", "-D", "--singleline"]
        flags += user_flags
        total_output: list[str] = []
        tool_bin = self.get_binary()

        try:
            subproc_args = [tool_bin] + flags + files
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )
            total_output.append(output)
        except subprocess.CalledProcessError as ex:
            logging.warning("Problem %d", ex.returncode)
            logging.warning("%s exception: %s", self.get_name(), ex.output)
            return None

        except OSError as ex:
            logging.warning("Couldn't find flawfinder executable! (%s)", ex)
            return None

        logging.debug("%s", total_output)

        return total_output

    def parse_output(
        self, total_output: list[str], package: Package | None = None
    ) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            total_output: List of output strings.
            package: The package being analyzed.

        Returns:
            List of issues.
        """
        flawfinder_re = r"(.+):(\d+):\s+\[(\d+)\]\s+(.+):\s*(.+)"
        parse: Pattern[str] = re.compile(flawfinder_re)
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
                            match.group(4),
                            int(match.group(3)),
                            match.group(5),
                            None,
                        )
                    )

        return issues
