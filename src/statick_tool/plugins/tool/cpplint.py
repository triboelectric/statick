"""Apply Cpplint tool and gather results."""

import logging
import os
import re
import subprocess
from typing import Match, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class CpplintToolPlugin(ToolPlugin):
    """Apply Cpplint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "cpplint"

    def get_binary(  # pylint: disable=unused-argument
        self, level: str | None = None, package: Package | None = None
    ) -> str:
        """Return the name of the tool binary.

        Args:
            level: The level of the scan.
            package: The package to scan.

        Returns:
            The name of the tool binary.
        """
        binary = self.get_name()
        if package is not None and "cpplint" in package:
            binary = package["cpplint"]

        return binary

    def scan(self, package: Package, level: str) -> list[Issue] | None:
        """Run tool and gather output.

        Args:
            package: The package to scan.
            level: The level of the scan.

        Returns:
            A list of issues found by the tool.
        """
        if "make_targets" not in package and "headers" not in package:
            return []

        if not package["make_targets"] and not package["headers"]:
            return []

        if "cpplint" not in package:
            logging.warning("  cpplint not found!")
            return None

        flags: list[str] = []
        flags += self.get_user_flags(level)
        cpplint = self.get_binary(package=package)

        files: list[str] = []
        if "make_targets" in package:
            for target in package["make_targets"]:
                files += target["src"]

        try:
            output = subprocess.check_output(
                [cpplint] + flags + files,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                logging.warning("cpplint failed! Returncode = %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find cpplint executable! (%s)", ex)
            return None

        logging.debug("%s", output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
                fid.write(output)

        issues: list[Issue] = self.parse_tool_output(output)
        return issues

    @classmethod
    def check_for_exceptions(cls, match: Match[str]) -> bool:
        """Manual exceptions.

        Args:
            match: The regex match object.

        Returns:
            True if the match is an exception, False otherwise.
        """
        if (
            match.group(1).endswith(".cpp") or match.group(1).endswith(".cc")
        ) and match.group(4) == "build/namespaces":
            # allow using namespace inside source files
            return True
        if match.group(4) == "build/namespaces" and "unnamed" in match.group(3):
            # ignore anonymous namespace warning
            return True
        if (
            "cfg/cpp" in match.group(1)
            and match.group(1).endswith("Config.h")
            and match.group(4) == "build/storage_class"
        ):
            # ignoring issue in auto-generated ROS code
            return True
        return False

    def parse_tool_output(self, output: str) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            output: The output from the tool.

        Returns:
            A list of issues found by the tool.
        """
        lint_re = r"(.+):(\d+):\s(.+)\s\[(.+)\]\s\[(\d+)\]"
        parse: Pattern[str] = re.compile(lint_re)
        issues: list[Issue] = []
        for line in output.splitlines():
            match: Match[str] | None = parse.match(line)
            if match and not self.check_for_exceptions(match):
                norm_path = os.path.normpath(match.group(1))
                issues.append(
                    Issue(
                        norm_path,
                        int(match.group(2)),
                        self.get_name(),
                        match.group(4),
                        int(match.group(5)),
                        match.group(3),
                        None,
                    )
                )
        return issues
