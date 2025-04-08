"""Do nothing, this is primarily useful for testing purposes."""

from importlib.metadata import version
from typing import Optional

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class DoNothingToolPlugin(ToolPlugin):
    """Do nothing, this is primarily useful for testing purposes."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "do_nothing"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return []

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
        return ""

    def get_version(self) -> str:
        """Figure out and return the version of the tool that's installed.

        Returns:
            Version of the tool.
        """
        return version("statick")

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
        return []

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

        return issues
