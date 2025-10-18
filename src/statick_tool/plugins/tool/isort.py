"""Apply isort tool and gather results.

The isort tool will only find if a file has issues with imports. To automatically fix
the issues you can run `isort <file>`.
"""

import logging
import subprocess

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class IsortToolPlugin(ToolPlugin):
    """Apply isort tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "isort"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return ["python_src"]

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
        tool_bin = "isort"
        flags: list[str] = ["--check-only"]
        flags += user_flags

        total_output: list[str] = []

        try:
            subproc_args = [tool_bin] + flags + files
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )
            total_output.append(output)

        except (IOError, OSError) as ex:
            logging.warning("isort binary failed: %s", tool_bin)
            logging.warning("Error = %s", ex.strerror)
            return []

        except subprocess.CalledProcessError as ex:
            logging.warning("isort binary failed: %s.", tool_bin)
            logging.warning("Returncode: %d", ex.returncode)
            logging.warning("%s exception: %s", self.get_name(), ex.output)
            total_output.append(ex.output)

        logging.debug("%s", total_output)

        return total_output

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
        issues: list[Issue] = []

        for output in total_output:
            # Skip output that contain only an empty string.
            if not output:
                continue
            msg = "Imports are incorrectly sorted and/or formatted."
            issues.append(
                Issue(
                    output,
                    0,
                    self.get_name(),
                    "formatting",
                    3,
                    msg,
                    None,
                )
            )

        return issues
