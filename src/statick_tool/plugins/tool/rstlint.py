"""Apply rst-lint tool and gather results."""

import logging

import restructuredtext_lint
from docutils.utils import SystemMessage

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class RstlintToolPlugin(ToolPlugin):
    """Apply rst-lint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            The name of the tool.
        """
        return "rstlint"

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
        return "rst-lint"

    # pylint: disable=too-many-locals
    def scan(self, package: Package, level: str) -> list[Issue] | None:
        """Run tool and gather output.

        Args:
            package: The package to scan.
            level: The level of the scan.

        Returns:
            A list of issues found by the tool.
        """
        flags: list[str] = []
        user_flags = self.get_user_flags(level)
        flags += user_flags

        files: list[str] = []
        if "rst_src" in package:
            files += package["rst_src"]

        total_output: list[SystemMessage] = []

        for src in files:
            output = restructuredtext_lint.lint_file(src, flags)
            total_output.extend(output)

        for output in total_output:
            logging.debug("%s", str(output))

        with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
            for output in total_output:
                fid.write(str(output))

        issues: list[Issue] = self.parse_tool_output(total_output)
        return issues

    # pylint: enable=too-many-locals

    def parse_tool_output(self, total_output: list[SystemMessage]) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            total_output: The output from the tool.

        Returns:
            A list of issues parsed from the output.
        """
        issues: list[Issue] = []

        # Have to ignore some type hints as they are an addition to SystemMessage
        # and not in the typeshed stubs.
        # https://github.com/twolfson/restructuredtext-lint#restructuredtext_lintlintcontent-filepathnone-rst_prolognone
        # https://github.com/python/typeshed/blob/master/stubs/docutils/docutils/utils/__init__.pyi
        for output in total_output:
            issues.append(
                Issue(
                    output.source,  # type: ignore
                    output.line,  # type: ignore
                    self.get_name(),
                    output.type,  # type: ignore
                    output.level,
                    output.message,  # type: ignore
                    None,
                )
            )
        return issues
