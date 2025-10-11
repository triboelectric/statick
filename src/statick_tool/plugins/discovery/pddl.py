"""Discover PDDL files to analyze."""

import logging

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class PDDLDiscoveryPlugin(DiscoveryPlugin):
    """Discover PDDL files to analyze."""

    def get_name(self) -> str:
        """Get name of discovery type.

        Returns:
            Name of the discovery type.
        """
        return "pddl"

    def scan(
        self, package: Package, level: str, exceptions: Exceptions | None = None
    ) -> None:
        """Scan package looking for PDDL files.

        Args:
            package: The package to scan.
            level: The level of scanning.
            exceptions: Optional exceptions to apply.
        """
        pddl_files: list[str] = []

        self.find_files(package)

        for file_dict in package.files.values():
            if file_dict["name"].endswith(".pddl"):
                pddl_files.append(file_dict["path"])

        logging.info("  %d PDDL files found.", len(pddl_files))
        if exceptions:
            original_file_count: int = len(pddl_files)
            pddl_files = exceptions.filter_file_exceptions_early(package, pddl_files)
            if original_file_count > len(pddl_files):
                logging.info(
                    "  After filtering, %d PDDL files will be scanned.", len(pddl_files)
                )

        package["pddl_domain_src"] = []
        package["pddl_problem_src"] = []
        for filename in pddl_files:
            if self.discover_pddl_file_type(filename) == "domain":
                package["pddl_domain_src"].append(filename)
            elif self.discover_pddl_file_type(filename) == "problem":
                package["pddl_problem_src"].append(filename)

    @classmethod
    def discover_pddl_file_type(cls, filename: str) -> str:
        """Determine the type of PDDL file that was discovered.

        Args:
            filename: The name of the file to check.

        Returns:
            The type of PDDL file.
        """
        with open(filename, encoding="utf-8") as f_pddl:
            for line in f_pddl.readlines():
                if "(define" in line and "domain" in line:
                    return "domain"
                if "(define" in line and "problem" in line:
                    return "problem"

        return ""
