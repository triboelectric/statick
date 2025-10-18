"""Apply bandit tool and gather results."""

import argparse
import csv
import logging
import subprocess

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class BanditToolPlugin(ToolPlugin):
    """Apply bandit tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "bandit"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments.

        Args:
            args: Flags for this plugin will be added to these existing arguments.
        """
        args.add_argument(
            "--bandit-bin", dest="bandit_bin", type=str, help="bandit binary path"
        )

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return ["python_src"]

    def get_binary(  # pylint: disable=unused-argument
        self, level: str | None = None, package: Package | None = None
    ) -> str:
        """Get tool binary name.

        Args:
            level: The level to run the tool at.
            package: The package being processed.

        Returns:
            The binary name.
        """
        binary = self.get_name()
        if self.plugin_context and self.plugin_context.args.bandit_bin is not None:
            binary = self.plugin_context.args.bandit_bin
        return binary

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
        bandit_bin = self.get_binary()

        flags: list[str] = ["--format=csv"]
        flags += user_flags

        try:
            output = subprocess.check_output(
                [bandit_bin] + flags + files,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )

        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                logging.warning("bandit failed! Returncode = %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", bandit_bin, ex)
            return None

        logging.debug("%s", output)
        return output.splitlines()

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

        # Copy output for modification
        output_minus_log = list(total_output)

        # Bandit prints a bunch of log messages out and you can't suppress
        # them, so iterate over the list until we find the CSV header
        for line in total_output:  # Intentionally total_output, not output_minus_log
            if line.startswith("filename"):
                # Found the CSV header, stop removing things
                break
            output_minus_log.remove(line)

        csvreader = csv.DictReader(output_minus_log)
        for csv_line in csvreader:
            severity = 1
            if csv_line["issue_confidence"] == "MEDIUM":
                severity = 3
            elif csv_line["issue_confidence"] == "HIGH":
                severity = 5
            issues.append(
                Issue(
                    csv_line["filename"],
                    int(csv_line["line_number"]),
                    self.get_name(),
                    csv_line["test_id"],
                    severity,
                    csv_line["issue_text"],
                    None,
                )
            )

        return issues
