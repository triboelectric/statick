"""Apply markdownlint tool and gather results."""

import logging
import re
import subprocess
from typing import Match, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class MarkdownlintToolPlugin(ToolPlugin):
    """Apply markdownlint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "markdownlint"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return ["md_src"]

    # pylint: disable=too-many-locals
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
        tool_bin = self.get_binary()

        tool_config = ".markdownlintrc"
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
            flags += ["-c", format_file_name]
        flags += user_flags

        total_output: list[str] = []

        try:
            exe = [tool_bin] + flags + files
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
                logging.warning("%s failed! Returncode = %d", tool_bin, ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None
            if ex.returncode == 1:  # markdownlint returns 1 upon linting errors
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
            package: The package being processed.

        Returns:
            List of issues found.
        """
        markdownlint_re = r"(.+):(\d+)\s([^\s]+)\s(.+)"
        markdownlint_re_with_col = r"(.+):(\d+):(\d+)\s([^\s]+)\s(.+)"
        parse: Pattern[str] = re.compile(markdownlint_re)
        parse_with_col: Pattern[str] = re.compile(markdownlint_re_with_col)
        issues: list[Issue] = []

        for output in total_output:
            for line in output.split("\n"):
                match_with_col: Match[str] | None = parse_with_col.match(line)
                if match_with_col:
                    issues.append(
                        Issue(
                            match_with_col.group(1),
                            int(match_with_col.group(2)),
                            self.get_name(),
                            match_with_col.group(4),
                            3,
                            match_with_col.group(5),
                            None,
                        )
                    )
                else:
                    match: Match[str] | None = parse.match(line)
                    if match:
                        issues.append(
                            Issue(
                                match.group(1),
                                int(match.group(2)),
                                self.get_name(),
                                match.group(3),
                                3,
                                match.group(4),
                                None,
                            )
                        )
        return issues
