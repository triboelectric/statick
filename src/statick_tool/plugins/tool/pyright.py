"""Apply pyright tool and gather results."""

import json
import logging
import subprocess
from typing import Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class PyrightToolPlugin(ToolPlugin):
    """Apply pyright tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "pyright"

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
            package: The package to process.
            level: The level to run the tool at.
            files: List of files to process.
            user_flags: List of user flags.

        Returns:
            List of output strings or None.
        """
        flags: list[str] = [
            "--outputjson",
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
            logging.warning("pyright binary failed: %s", tool_bin)
            logging.warning("Error = %s", ex.strerror)
            return []

        except subprocess.CalledProcessError as ex:
            # pyright returns 1 if issues are found. That is what we are looking for,
            # so we do not need to log this as an error.
            if ex.returncode != 1:
                logging.warning("pyright binary failed: %s.", tool_bin)
                logging.warning("Returncode: %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
            output = ex.output

        total_output.append(output)

        logging.debug("%s", total_output)

        return total_output

    # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements

    def parse_output(
        self, total_output: list[str], package: Optional[Package] = None
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
            try:
                data = json.loads(output)
            except json.JSONDecodeError as ex:
                logging.warning("JSONDecodeError: %s", ex)
                continue
            except ValueError as ex:
                logging.warning("ValueError: %s", ex)
                continue
            try:
                data = data["generalDiagnostics"]
            except KeyError:
                logging.warning("No generalDiagnostics found in output.")
                continue
            for issue in data:
                severity = 1
                if issue["severity"] == "warning":
                    severity = 3
                if issue["severity"] == "error":
                    severity = 5

                issues.append(
                    Issue(
                        issue["file"],
                        int(issue["range"]["start"]["line"]),
                        self.get_name(),
                        issue["rule"],
                        severity,
                        issue["message"],
                        None,
                    )
                )
        return issues
