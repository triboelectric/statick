"""Discover shell files to analyze."""

import logging
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class ShellDiscoveryPlugin(DiscoveryPlugin):
    """Discover shell files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type.

        Returns:
            Name of the discovery type.
        """
        return "shell"

    def scan(
        self, package: Package, level: str, exceptions: Exceptions | None = None
    ) -> None:
        """Scan package looking for shell files.

        Args:
            package: The package to scan.
            level: The level of scanning.
            exceptions: Optional exceptions to apply.
        """
        shell_files: list[str] = []
        shell_extensions = (".sh", ".bash", ".zsh", ".csh", ".ksh", ".dash")
        shell_output = ("shell script", "dash script", "zsh script")

        self.find_files(package)

        for file_dict in package.files.values():
            if file_dict["name"].endswith(shell_extensions):
                shell_files.append(file_dict["path"])

            if any(item in file_dict["file_cmd_out"] for item in shell_output):
                shell_files.append(file_dict["path"])

        shell_files = list(OrderedDict.fromkeys(shell_files))

        logging.info("  %d shell files found.", len(shell_files))
        if exceptions:
            original_file_count = len(shell_files)
            shell_files = exceptions.filter_file_exceptions_early(package, shell_files)
            if original_file_count > len(shell_files):
                logging.info(
                    "  After filtering, %d shell files will be scanned.",
                    len(shell_files),
                )

        package["shell_src"] = shell_files
