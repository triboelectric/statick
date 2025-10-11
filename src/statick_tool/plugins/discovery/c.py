"""Discover C files to analyze."""

import logging
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class CDiscoveryPlugin(DiscoveryPlugin):
    """Discover C/C++ files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type.

        Returns:
            Name of the discovery type.
        """
        return "C"

    def scan(
        self, package: Package, level: str, exceptions: Exceptions | None = None
    ) -> None:
        """Scan package looking for C files.

        Args:
            package: The package to scan.
            level: The level of scanning.
            exceptions: Optional exceptions to apply.
        """
        c_files: list[str] = []
        c_extensions = (".c", ".cc", ".cpp", ".cxx", ".h", ".hxx", ".hpp")
        c_output = ("c source", "c program", "c++ source")

        self.find_files(package)

        for file_dict in package.files.values():
            if file_dict["name"].endswith(c_extensions):
                c_files.append(file_dict["path"])

            if any(
                item in file_dict["file_cmd_out"] for item in c_output
            ) and not file_dict["name"].endswith(".cfg"):
                c_files.append(file_dict["path"])

        c_files = list(OrderedDict.fromkeys(c_files))

        logging.info("  %d C/C++ files found.", len(c_files))
        if exceptions:
            original_file_count = len(c_files)
            c_files = exceptions.filter_file_exceptions_early(package, c_files)
            if original_file_count > len(c_files):
                logging.info(
                    "  After filtering, %d C/C++ files will be scanned.", len(c_files)
                )

        package["c_src"] = c_files
