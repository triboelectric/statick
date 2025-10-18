"""Discover XML files to analyze."""

import logging
from collections import OrderedDict

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class XMLDiscoveryPlugin(DiscoveryPlugin):
    """Discover XML files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type.

        Returns:
            Name of the discovery type.
        """
        return "xml"

    def scan(
        self, package: Package, level: str, exceptions: Exceptions | None = None
    ) -> None:
        """Scan package looking for XML files.

        Args:
            package: The package to scan.
            level: The level of scanning.
            exceptions: Optional exceptions to apply.
        """
        xml_files: list[str] = []
        xml_extensions: tuple[str, str] = (".xml", ".launch")

        self.find_files(package)

        for file_dict in package.files.values():
            if file_dict["name"].endswith(xml_extensions):
                xml_files.append(file_dict["path"])

        xml_files = list(OrderedDict.fromkeys(xml_files))

        logging.info("  %d XML files found.", len(xml_files))
        if exceptions:
            original_file_count = len(xml_files)
            xml_files = exceptions.filter_file_exceptions_early(package, xml_files)
            if original_file_count > len(xml_files):
                logging.info(
                    "  After filtering, %d XML files will be scanned.", len(xml_files)
                )

        package["xml"] = xml_files
