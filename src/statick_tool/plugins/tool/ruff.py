"""Apply ruff tool and gather results."""

import json
import logging
import subprocess

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class RuffToolPlugin(ToolPlugin):
    """Apply ruff tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            The name of the tool.
        """
        return "ruff"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            A list of file types.
        """
        return ["python_src"]

    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> list[str] | None:
        """Run tool and gather output.

        Args:
            package: The package to scan.
            level: The level of the scan.
            files: The files to scan.
            user_flags: The user flags to pass to the tool.

        Returns:
            The output from the tool.
        """
        flags: list[str] = ["check", "--output-format", "json"]
        flags += user_flags
        total_output: list[str] = []

        try:
            subproc_args = ["ruff"] + flags + files
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )
        except subprocess.CalledProcessError as ex:
            output = ex.output
        except OSError as ex:
            logging.warning("Couldn't find ruff executable! (%s)", ex)
            return None

        total_output.append(output)

        logging.debug("%s", total_output)

        return total_output

    def parse_output(
        self, total_output: list[str], package: Package | None = None
    ) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            total_output: The output from the tool.
            package: The package to scan.

        Returns:
            A list of issues parsed from the output.
        """
        issues: list[Issue] = []

        for output_str in total_output:
            try:
                results = json.loads(output_str.strip("[]"))
            except json.JSONDecodeError as ex:
                logging.error("Failed to decode ruff output as JSON: %s", ex)
                continue

            filename = results.get("filename")
            line = results.get("location", {}).get("row", 1)
            issue_type = results.get("code", "")
            message = results.get("message", "")
            issues.append(
                Issue(
                    filename,
                    line,
                    self.get_name(),
                    issue_type,
                    5,
                    message,
                    None,
                )
            )

        return issues
