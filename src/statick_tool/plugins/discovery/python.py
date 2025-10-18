"""Discover python files to analyze."""

import logging
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class PythonDiscoveryPlugin(DiscoveryPlugin):
    """Discover python files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type.

        Returns:
            Name of the discovery type.
        """
        return "python"

    def scan(
        self, package: Package, level: str, exceptions: Exceptions | None = None
    ) -> None:
        """Scan package looking for python files.

        Args:
            package: The package to scan.
            level: The level of scanning.
            exceptions: Optional exceptions to apply.
        """
        python_files: list[str] = []

        self.find_files(package)

        for file_dict in package.files.values():
            if file_dict["name"].endswith(".py"):
                python_files.append(file_dict["path"])
            elif "python script" in file_dict["file_cmd_out"] and not file_dict[
                "name"
            ].endswith(".cfg"):
                python_files.append(file_dict["path"])

        python_files = list(OrderedDict.fromkeys(python_files))

        logging.info("  %d python files found.", len(python_files))
        if exceptions:
            original_file_count = len(python_files)
            python_files = exceptions.filter_file_exceptions_early(
                package, python_files
            )
            if original_file_count > len(python_files):
                logging.info(
                    "  After filtering, %d python files will be scanned.",
                    len(python_files),
                )

        package["python_src"] = python_files
