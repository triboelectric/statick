"""Apply make tool and gather results."""

import logging
import re
import subprocess
from typing import Any, Match, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class MakeToolPlugin(ToolPlugin):
    """Apply Make tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "make"

    def scan(self, package: Package, level: str) -> list[Issue] | None:
        """Run tool and gather output.

        Args:
            package: The package to process.
            level: The level to run the tool at.

        Returns:
            List of issues found or None.
        """
        if "make_targets" not in package or not package["make_targets"]:
            logging.info("  Skipping make. No targets.")
            return []

        tool_bin = self.get_binary()

        output = None
        make_args: list[str] = [tool_bin, "statick_cmake_target"]

        try:
            output = subprocess.check_output(
                [tool_bin, "clean"], universal_newlines=True
            )
            output = subprocess.check_output(
                make_args, stderr=subprocess.STDOUT, universal_newlines=True
            )

        except subprocess.CalledProcessError as ex:
            output = ex.output
            logging.warning("Make failed! Returncode = %d", ex.returncode)
            logging.warning("%s exception: %s", self.get_name(), ex.output)
            return None

        except OSError as ex:
            logging.warning("Couldn't find make executable! (%s)", ex)
            return None

        logging.debug("%s", output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
                fid.write(output)

        issues: list[Issue] = self.parse_package_output(package, output)
        return issues

    @classmethod
    def check_for_exceptions(cls, match: Match[str]) -> bool:
        """Manual exceptions.

        Args:
            match: The regex match object.

        Returns:
            Boolean indicating if the match is an exception.
        """
        return match.group(4) == "note"

    @classmethod
    def filter_matches(cls, matches: Any, package: Package) -> Any:
        """Filter matches.

        Args:
            matches: List of matches.
            package: The package being processed.

        Returns:
            Filtered list of matches.
        """
        i = 0
        result = []
        while i < len(matches):
            cur_match = matches[i]
            if "overloaded-virtual" in cur_match[4] and i + 1 < len(matches):
                next_match = matches[i + 1]
                if next_match[0].startswith(package.path):
                    result.append(
                        (
                            next_match[0],
                            next_match[1],
                            next_match[2],
                            cur_match[3],
                            cur_match[4] + next_match[4],
                        )
                    )
                i += 1  # Skip next match.
            else:
                result.append(cur_match)
            i += 1
        return result

    def parse_package_output(  # pylint: disable=too-many-locals, too-many-branches
        self, package: Package, output: str
    ) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            package: The package being processed.
            output: The output from the tool.

        Returns:
            List of issues found.
        """
        make_re = r"(.+):(\d+):(\d+):\s(.+):\s(.+)"
        make_warning_re = r".*\[(.+)\].*"
        parse: Pattern[str] = re.compile(make_re)
        warning_parse: Pattern[str] = re.compile(make_warning_re)
        matches: Any = []
        # Load the plugin mapping if possible
        warnings_mapping = self.load_mapping()
        for line in output.splitlines():
            match: Match[str] | None = parse.match(line)
            if match and not self.check_for_exceptions(match):
                matches.append(match.groups())

        filtered_matches = self.filter_matches(matches, package)
        issues: list[Issue] = []
        for item in filtered_matches:
            cert_reference = None
            warning_list = warning_parse.match(item[4])
            if (
                warning_list is not None
                and warning_list.groups("1")[0] in warnings_mapping
            ):
                cert_reference = warnings_mapping[warning_list.groups("1")[0]]

            if warning_list is None:
                # Something's gone wrong if we don't match the [warning] format
                if "fatal error" in item[3]:
                    category = "fatal-error"
                else:
                    category = "unknown-error"
            else:
                category = warning_list.groups("1")[0]

            if item[3].lower() == "warning":
                severity = 3
            elif item[3].lower() == "error":
                severity = 5
            elif item[3].lower() == "fatal error":
                severity = 5
            else:
                severity = 3

            issue = Issue(
                item[0],
                int(item[1]),
                self.get_name(),
                category,
                severity,
                item[4],
                cert_reference,
            )
            if issue not in issues:
                issues.append(issue)

        lines = output.splitlines()
        if "collect2: ld returned 1 exit status" in lines:
            issues.append(
                Issue(
                    "Linker",
                    0,
                    self.get_name(),
                    "linker",
                    5,
                    "Linking failed",
                    None,
                )
            )
        return issues
