"""Apply dockerfilelint tool and gather results."""

import json
import logging
import pathlib
import subprocess

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class DockerfileLintToolPlugin(ToolPlugin):
    """Apply dockerfilelint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "dockerfilelint"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return ["dockerfile_src"]

    # pylint: disable=too-many-locals
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
        tool_bin = self.get_binary()

        tool_config = ".dockerfilelintrc"
        user_config = None
        if self.plugin_context is not None:
            user_config = self.plugin_context.config.get_tool_config(
                self.get_name(), level, "config"
            )
        if user_config is not None:
            tool_config = user_config

        format_file_name = None
        format_file_path = None
        if self.plugin_context is not None:
            format_file_name = self.plugin_context.resources.get_file(tool_config)
            if format_file_name is not None:
                format_file_path = pathlib.Path(format_file_name).resolve().parent
        flags: list[str] = []
        if format_file_path is not None:
            flags += ["-c", str(format_file_path)]
        flags += ["-o", "json"]
        flags += user_flags

        total_output: list[str] = []

        try:
            exe = [tool_bin] + flags + files
            output = subprocess.check_output(
                exe, stderr=subprocess.STDOUT, universal_newlines=True
            )
            total_output.append(output)

        except subprocess.CalledProcessError as ex:
            # dockerfilelint returns the number of linting errors as the return code
            if ex.returncode > 0:
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

    # pylint: enable=too-many-locals

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
        issues: list[Issue] = []

        # pylint: disable=too-many-nested-blocks
        for output in total_output:
            for line in output.split("\n"):
                if line:
                    try:
                        err_dict = json.loads(line)["files"]
                        for file_issues in err_dict:
                            for issue in file_issues["issues"]:
                                severity_str = issue["category"]
                                severity = 1
                                if severity_str == "Possible Bug":
                                    severity = 3
                                elif severity_str == "Deprecation":
                                    severity = 5
                                issues.append(
                                    Issue(
                                        file_issues["file"],
                                        int(issue["line"]),
                                        self.get_name(),
                                        issue["title"],
                                        severity,
                                        issue["description"],
                                        None,
                                    )
                                )

                    except ValueError as ex:
                        issues.append(
                            Issue(
                                "EXCEPTION",
                                0,
                                self.get_name(),
                                "ValueError",
                                5,
                                str(ex) + ", on line: " + line,
                                None,
                            )
                        )
        # pylint: enable=too-many-nested-blocks
        return issues
