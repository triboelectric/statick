"""Apply docformatter tool and gather results."""

import logging
import os
import re
import subprocess
from typing import Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class DocformatterToolPlugin(ToolPlugin):
    """Apply docformatter tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "docformatter"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return ["python_src"]

    # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements
    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> Optional[list[str]]:
        """Run tool and gather output.

        Args:
            package: The package being analyzed.
            level: The analysis level.
            files: List of files to process.
            user_flags: List of user flags.

        Returns:
            List of output strings or None.
        """
        flags: list[str] = ["-c"]
        flags += user_flags
        tool_bin = self.get_binary()
        total_output: list[str] = []

        try:
            subproc_args = [tool_bin] + flags + files
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )

        except (IOError, OSError) as ex:
            logging.warning("docformatter binary failed: %s", tool_bin)
            logging.warning("Error = %s", ex.strerror)
            return []

        except subprocess.CalledProcessError as ex:
            if ex.returncode == 3:
                output = ex.output
            else:
                logging.warning("docformatter binary failed: %s.", tool_bin)
                logging.warning("Returncode: %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                output = ex.output

        total_output.append(output)

        logging.debug("%s", total_output)

        return total_output

    # pylint: enable=too-many-locals, too-many-branches, too-many-return-statements

    def parse_output(
        self, total_output: list[str], package: Optional[Package] = None
    ) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            total_output: List of output strings.
            package: The package being analyzed.

        Returns:
            List of issues.
        """
        # Gives relative path to file.
        tool_re = r"(.+)[\\/](.+)"
        parse: Pattern[str] = re.compile(tool_re)
        issues: list[Issue] = []

        for output in total_output:
            lines = output.splitlines()
            for line in lines:
                match: Optional[Match[str]] = parse.match(line)
                if match:
                    issues.append(
                        Issue(
                            os.path.join(match.group(1), match.group(2)),
                            0,
                            self.get_name(),
                            "format",
                            3,
                            "would reformat",
                            None,
                        )
                    )
        return issues
