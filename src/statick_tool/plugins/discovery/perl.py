"""Discover Perl files to analyze."""

import logging
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class PerlDiscoveryPlugin(DiscoveryPlugin):
    """Discover Perl files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type.

        Returns:
            Name of the discovery type.
        """
        return "perl"

    def scan(
        self, package: Package, level: str, exceptions: Exceptions | None = None
    ) -> None:
        """Scan package looking for Perl files.

        Args:
            package: The package to scan.
            level: The level of scanning.
            exceptions: Optional exceptions to apply.
        """
        perl_files: list[str] = []

        self.find_files(package)

        for file_dict in package.files.values():
            if (
                file_dict["name"].endswith(".pl")
                or "perl script" in file_dict["file_cmd_out"]
            ):
                perl_files.append(file_dict["path"])

        perl_files = list(OrderedDict.fromkeys(perl_files))

        logging.info("  %d Perl files found.", len(perl_files))
        if exceptions:
            original_file_count = len(perl_files)
            perl_files = exceptions.filter_file_exceptions_early(package, perl_files)
            if original_file_count > len(perl_files):
                logging.info(
                    "  After filtering, %d perl files will be scanned.", len(perl_files)
                )

        package["perl_src"] = perl_files
