"""Apply cppcheck tool and gather results."""

import argparse
import logging
import os
import re
import subprocess
from typing import Match, Pattern

from packaging.version import Version

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class CppcheckToolPlugin(ToolPlugin):
    """Apply cppcheck tool and gather results."""

    # pylint: disable=super-init-not-called
    def __init__(self) -> None:
        """Initialize cppcheck extensions."""
        self.valid_extensions = [".h", ".hpp", ".c", ".cc", ".cpp", ".cxx"]

    # pylint: enable=super-init-not-called

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "cppcheck"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments.

        Args:
            args: Flags for this plugin will be added to these existing arguments.
        """
        args.add_argument(
            "--cppcheck-bin", dest="cppcheck_bin", type=str, help="cppcheck binary path"
        )

    def get_binary(  # pylint: disable=unused-argument
        self, level: str | None = None, package: Package | None = None
    ) -> str:
        """Get tool binary name.

        Args:
            level: The level of the scan.
            package: The package to scan.

        Returns:
            The name of the tool binary.
        """
        binary = self.get_name()
        if (
            self.plugin_context is not None
            and self.plugin_context.args.cppcheck_bin is not None
        ):
            binary = self.plugin_context.args.cppcheck_bin

        return binary

    def parse_version(self, version_str: str) -> str:
        """Parse version of tool.

        If no version is found the function returns "0.0".

        Args:
            version_str: The version string to parse.

        Returns:
            The parsed version string.
        """
        version = "0.0"
        ver_re = r"(.+) ([0-9]*\.?[0-9]+)"
        parse: Pattern[str] = re.compile(ver_re)
        match: Match[str] | None = parse.match(version_str)
        if match:
            version = match.group(2)
        return version

    # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements
    def scan(self, package: Package, level: str) -> list[Issue] | None:
        """Run tool and gather output.

        Args:
            package: The package to scan.
            level: The level of the scan.

        Returns:
            A list of issues found by the tool.
        """
        if (
            "make_targets" not in package and "headers" not in package
        ) or self.plugin_context is None:
            return []

        flags: list[str] = [
            "--report-progress",
            "--verbose",
            "--inline-suppr",
            "--language=c++",
            "--template=[{file}:{line}]: ({severity} {id}) {message}",
        ]
        flags += self.get_user_flags(level)
        user_version = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "version"
        )

        cppcheck_bin = self.get_binary()

        try:
            version = self.parse_version(self.get_version())
            # If specific version is not specified just use the installed version.
            if user_version is not None and Version(version) != Version(user_version):
                logging.warning(
                    "You need version %s of cppcheck, but you have %s. "
                    "See README.md for instructions on how to install the "
                    "proper version",
                    user_version,
                    version,
                )
                return None

        except OSError as ex:
            logging.warning("Cppcheck not found! (%s)", ex)
            return None

        files: list[str] = []
        include_dirs: list[str] = []
        if "make_targets" in package:
            for target in package["make_targets"]:
                files += target["src"]
                if "include_dirs" in target:
                    for include_dir in target["include_dirs"]:
                        if include_dir not in include_dirs:
                            include_dirs.append(include_dir)
        if "headers" in package:
            files += package["headers"]

        if not files:
            return []

        include_args = []
        for include_dir in include_dirs:
            if package.path in include_dir:
                include_args.append("-I")
                include_args.append(include_dir)

        try:
            output = subprocess.check_output(
                [cppcheck_bin] + flags + include_args + files,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as ex:
            output = ex.output
            logging.warning("cppcheck failed! Returncode = %d", ex.returncode)
            logging.warning("%s exception: %s", self.get_name(), ex.output)
            return None

        logging.debug("%s", output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
                fid.write(output)

        issues: list[Issue] = self.parse_tool_output(output)
        return issues

    # pylint: enable=too-many-locals, too-many-branches, too-many-return-statements

    @classmethod
    def check_for_exceptions(cls, match: Match[str]) -> bool:
        """Manual exceptions.

        Args:
            match: The regex match object.

        Returns:
            True if the match is an exception, False otherwise.
        """
        # Sometimes you can't fix variableScope in old c code
        if match.group(1).endswith(".c") and match.group(4) == "variableScope":
            return True
        return False

    def parse_tool_output(self, output: str) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            output: The output from the tool.

        Returns:
            A list of issues found by the tool.
        """
        cppcheck_re = r"\[(.+):(\d+)\]:\s\((.+?)\s(.+?)\)\s(.+)"
        parse: Pattern[str] = re.compile(cppcheck_re)
        issues: list[Issue] = []
        warnings_mapping = self.load_mapping()
        for line in output.splitlines():
            match: Match[str] | None = parse.match(line)
            if (
                match
                and line[1] != "*"
                and match.group(3) != "information"
                and not self.check_for_exceptions(match)
            ):
                dummy, extension = os.path.splitext(match.group(1))
                if extension in self.valid_extensions:
                    cert_reference = None
                    if match.group(4) in warnings_mapping:
                        cert_reference = warnings_mapping[match.group(4)]
                    issues.append(
                        Issue(
                            match.group(1),
                            int(match.group(2)),
                            self.get_name(),
                            match.group(3) + "/" + match.group(4),
                            5,
                            match.group(5),
                            cert_reference,
                        )
                    )
        return issues
