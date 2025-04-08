"""Apply dockerfile-lint tool and gather results."""

import json
import logging
import subprocess
from typing import Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class DockerfileULintToolPlugin(ToolPlugin):
    """Apply dockerfile-lint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "dockerfile-lint"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return ["dockerfile_src"]

    def get_binary(  # pylint: disable=unused-argument
        self, level: Optional[str] = None, package: Optional[Package] = None
    ) -> str:
        """Get tool binary name.

        Args:
            level: The analysis level.
            package: The package being analyzed.

        Returns:
            Name of the tool binary.
        """
        return "dockerfile_lint"

    def get_version(self) -> str:
        """Figure out and return the version of the tool that's installed.

        Returns:
            Version of the tool or "Unknown" if not found.
        """
        return self.get_version_from_npm()

    # pylint: disable=too-many-locals
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
        tool_bin = self.get_binary()

        tool_config = "dockerfile_lint_rules.yaml"
        user_config = None
        if self.plugin_context is not None:
            user_config = self.plugin_context.config.get_tool_config(
                self.get_name(), level, "config"
            )
        if user_config is not None:
            tool_config = user_config

        format_file_name = None
        if self.plugin_context is not None:
            format_file_name = self.plugin_context.resources.get_file(tool_config)
        flags: list[str] = []
        if format_file_name is not None:
            flags += ["-r", format_file_name]
        flags += ["--json"]
        flags += user_flags

        total_output: list[str] = []

        for src in files:
            try:
                exe = [tool_bin] + flags + ["-f", src]
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                total_output.append(self.add_filename(output, src))

            except subprocess.CalledProcessError as ex:
                # dockerfilelint returns the number of linting errors as the return code
                if ex.returncode > 0:
                    total_output.append(self.add_filename(ex.output, src))
                else:
                    logging.warning(
                        "%s failed! Returncode = %d", tool_bin, ex.returncode
                    )
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None

            except OSError as ex:
                logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
                return None

        for output in total_output:
            logging.debug("%s", output)

        return total_output

    # pylint: enable=too-many-locals

    @classmethod
    def add_filename(cls, output: str, src: str) -> str:
        """Add the filename to the json output.

        This is because dockerfile-lint does not include the filename in the output.

        Some warnings and errors are included in the tool output, but they are not in
        json format. Those lines start with a "(". Any line that does not start with a
        "(" is considered to be a line of output.

        Args:
            output: The output string.
            src: The source file.

        Returns:
            Updated output string.
        """
        updated_output = ""
        for line in output.splitlines():
            if not line.startswith("("):
                updated_output = updated_output + line + "\n"
        try:
            json_dict = json.loads(updated_output)
            json_dict["filename"] = src
            return json.dumps(json_dict)
        except ValueError as ex:
            logging.warning("ValueError: %s", ex)
            return updated_output

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
        issues: list[Issue] = []

        # pylint: disable=too-many-nested-blocks
        for output in total_output:
            try:
                err_dict = json.loads(output)
                for file_issues in [
                    err_dict["error"]["data"],
                    err_dict["warn"]["data"],
                    err_dict["info"]["data"],
                ]:
                    for issue in file_issues:
                        severity_str = issue["level"]
                        severity = 1
                        if severity_str == "warn":
                            severity = 3
                        elif severity_str == "error":
                            severity = 5

                        message = issue["message"]
                        if "description" in issue:
                            message += ": " + issue["description"]

                        title = severity_str
                        line = -1
                        if "line" in issue:
                            line = int(issue["line"])
                        if "label" in issue:
                            title = issue["label"]

                        issues.append(
                            Issue(
                                err_dict["filename"],
                                line,
                                self.get_name(),
                                title,
                                severity,
                                message,
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
                        str(ex),
                        None,
                    )
                )
        # pylint: enable=too-many-nested-blocks
        return issues
