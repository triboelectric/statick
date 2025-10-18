"""Apply htmllint tool and gather results."""

import logging
import re
import subprocess
from typing import Match, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class HTMLLintToolPlugin(ToolPlugin):
    """Apply HTML tidy tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "htmllint"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return ["html_src"]

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

        tool_config = ".htmllintrc"
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
            flags += ["--rc", format_file_name]
        flags += user_flags

        total_output: list[str] = []

        for src in files:
            try:
                exe = [tool_bin] + flags + [src]
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                total_output.append(output)

            except subprocess.CalledProcessError as ex:
                if (
                    "Error: Cannot find module" in ex.output
                    or "Require stack:" in ex.output
                ):
                    # nodejs cannot find a module and threw an error
                    # this results in the same returncode `1` that markdownlint
                    # uses to indicate the presence of linting issues.
                    logging.warning(
                        "%s failed! Returncode = %d", tool_bin, ex.returncode
                    )
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None

                # tool returns 1 upon warnings and 2 upon errors
                if ex.returncode not in [1, 2]:
                    logging.warning(
                        "%s failed! Returncode = %d", tool_bin, ex.returncode
                    )
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None

                total_output.append(ex.output)

            except OSError as ex:
                logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
                return None

        for output in total_output:
            logging.debug("%s", output)

        return total_output

    def parse_output(
        self, total_output: list[str], package: Package | None = None
    ) -> list[Issue]:
        """Parse tool output and report issues."""
        re_str = r"(.+):\s.+\s(\d+),\s.+,\s(.+)"
        parse: Pattern[str] = re.compile(re_str)
        issues: list[Issue] = []

        for output in total_output:
            lines = output.split("\n")
            for line in lines:
                match: Match[str] | None = parse.match(line)
                if match:
                    filename = match.group(1)
                    line_number = int(match.group(2))
                    issue_type = "format"
                    message = match.group(3)
                    issues.append(
                        Issue(
                            filename,
                            line_number,
                            self.get_name(),
                            issue_type,
                            3,
                            message,
                            None,
                        )
                    )
        return issues
