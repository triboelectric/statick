"""Discover HTML files to analyze."""

import logging
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class HTMLDiscoveryPlugin(DiscoveryPlugin):
    """Discover HTML files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type.

        Returns:
            Name of the discovery type.
        """
        return "html"

    def scan(
        self, package: Package, level: str, exceptions: Exceptions | None = None
    ) -> None:
        """Scan package looking for HTML files.

        Args:
            package: The package to scan.
            level: The level of scanning.
            exceptions: Optional exceptions to apply.
        """
        src_files: list[str] = []

        self.find_files(package)

        for file_dict in package.files.values():
            if (
                file_dict["name"].endswith(".html")
                or "html document" in file_dict["file_cmd_out"]
            ):
                src_files.append(file_dict["path"])

        src_files = list(OrderedDict.fromkeys(src_files))

        logging.info("  %d HTML source files found.", len(src_files))
        if exceptions:
            original_file_count = len(src_files)
            src_files = exceptions.filter_file_exceptions_early(package, src_files)
            if original_file_count > len(src_files):
                logging.info(
                    "  After filtering, %d HTML files will be scanned.", len(src_files)
                )

        package["html_src"] = src_files
