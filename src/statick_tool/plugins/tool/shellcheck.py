"""Apply shellcheck tool and gather results.

The output from the tool is collected in JSON format to facilitate parsing.
"""

import argparse
import json
import logging
import subprocess
from typing import Any

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ShellcheckToolPlugin(ToolPlugin):
    """Apply shellcheck tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            The name of the tool.
        """
        return "shellcheck"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments.

        Args:
            args: Flags for this plugin will be added to these existing arguments.
        """
        args.add_argument(
            "--shellcheck-bin",
            dest="shellcheck_bin",
            type=str,
            help="shellcheck binary path",
        )

    def get_binary(  # pylint: disable=unused-argument
        self, level: str | None = None, package: Package | None = None
    ) -> str:
        """Get tool binary name.

        Args:
            level: The level of the scan.
            package: The package to scan.

        Returns:
            The binary name of the tool.
        """
        binary = self.get_name()
        if self.plugin_context and self.plugin_context.args.shellcheck_bin is not None:
            binary = self.plugin_context.args.shellcheck_bin
        return binary

    def scan(self, package: Package, level: str) -> list[Issue] | None:
        """Run tool and gather output.

        Args:
            package: The package to scan.
            level: The level of the scan.

        Returns:
            A list of issues found by the tool.
        """
        if "shell_src" not in package or not package["shell_src"]:
            return []

        shellcheck_bin = self.get_binary()

        # Get output in JSON format.
        flags: list[str] = ["-f", "json"]
        flags += self.get_user_flags(level)

        files: list[str] = []
        if "shell_src" in package:
            files += package["shell_src"]

        try:
            subproc_args = [shellcheck_bin] + flags + files
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )

        # We expect a CalledProcessError if issues are discovered by the tool.
        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                logging.warning("shellcheck failed! Returncode = %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", shellcheck_bin, ex)
            return None

        logging.debug("%s", output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
                fid.write(output)

        issues: list[Issue] = self.parse_json_output(json.loads(output))
        return issues

    def parse_json_output(self, output: Any) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            output: The JSON output from the tool.

        Returns:
            A list of issues parsed from the output.
        """
        issues: list[Issue] = []
        for item in output:
            if (
                "level" not in item
                or "file" not in item
                or "line" not in item
                or "code" not in item
                or "message" not in item
            ):
                logging.debug("  Found invalid shellcheck output: %s", item)
                continue
            if item["level"] == "style":
                severity = 1
            elif item["level"] == "info":
                severity = 1
            elif item["level"] == "warning":
                severity = 3
            elif item["level"] == "error":
                severity = 5
            else:
                severity = 3

            issue = Issue(
                item["file"],
                int(item["line"]),
                self.get_name(),
                "SC" + str(item["code"]),
                severity,
                item["message"],
                None,
            )

            issues.append(issue)

        return issues
