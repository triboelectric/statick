"""Apply clang-format tool and gather results."""

import argparse
import difflib
import logging
import os
import re
import subprocess
from typing import Match, Optional, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugins.tool.clang_format_parser import ClangFormatXMLParser
from statick_tool.tool_plugin import ToolPlugin


class ClangFormatToolPlugin(ToolPlugin):
    """Apply clang-format tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "clang-format"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments.

        Args:
            args: Flags for this plugin will be added to these existing arguments.
        """
        args.add_argument(
            "--clang-format-bin",
            dest="clang_format_bin",
            type=str,
            help="clang-format binary path",
        )
        args.add_argument(
            "--clang-format-raise-exception",
            dest="clang_format_raise_exception",
            action="store_true",
            help="clang-format raise exception on mismatched " "configuration file",
        )
        args.add_argument(
            "--clang-format-ignore-exception",
            dest="clang_format_raise_exception",
            action="store_false",
            help="clang-format ignore exception on mismatched " "configuration file",
        )
        args.set_defaults(clang_format_raise_exception=True)
        args.add_argument(
            "--clang-format-issue-per-line",
            dest="clang_format_issue_per_line",
            action="store_true",
            help="clang-format will report an issue per line of diff instead of per file",
        )

    def get_binary(
        self, level: Optional[str] = None, package: Optional[Package] = None
    ) -> str:
        """Return the name of the tool binary.

        Args:
            level: The level of the scan.
            package: The package to scan.

        Returns:
            The name of the tool binary.
        """
        user_version = None
        if level is not None and self.plugin_context:
            user_version = self.plugin_context.config.get_tool_config(
                self.get_name(), level, "version"
            )

        binary = self.get_name()
        if user_version is not None:
            binary = f"{binary}-{user_version}"

        # If the user explicitly specifies a binary, let that override the user_version
        if (
            self.plugin_context
            and self.plugin_context.args.clang_format_bin is not None
        ):
            binary = self.plugin_context.args.clang_format_bin

        return binary

    def scan(  # pylint: disable=too-many-return-statements, too-many-branches
        self, package: Package, level: str
    ) -> Optional[
        list[Issue]
    ]:  # pylint: disable=too-many-locals, too-many-branches, too-many-return-statements
        """Run tool and gather output.

        Args:
            package: The package to scan.
            level: The level of the scan.

        Returns:
            A list of issues found by the tool.
        """
        if "make_targets" not in package and "headers" not in package:
            return []

        clang_format_bin = self.get_binary(level=level)

        files: list[str] = []
        if "make_targets" in package:
            for target in package["make_targets"]:
                files += target["src"]
        if "headers" in package:
            files += package["headers"]

        check: Optional[bool] = self.check_configuration(clang_format_bin)
        if check is None:
            return None
        if not check:
            return []

        total_output: list[str] = []

        try:
            for src in files:
                output = subprocess.check_output(
                    [clang_format_bin, src, "-output-replacements-xml"],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                )
                if (
                    not self.plugin_context
                    or not self.plugin_context.args.clang_format_issue_per_line
                ):
                    output = src + "\n" + output
                if (
                    self.plugin_context
                    and self.plugin_context.args.clang_format_raise_exception
                ):
                    total_output.append(output)

        except (IOError, OSError) as ex:
            logging.warning("clang-format binary failed: %s", clang_format_bin)
            logging.warning("%s exception: %s", self.get_name(), ex.strerror)
            if (
                self.plugin_context
                and self.plugin_context.args.clang_format_raise_exception
            ):
                return None
            return []

        except subprocess.CalledProcessError as ex:
            logging.warning("clang-format binary failed: %s.", clang_format_bin)
            logging.warning("Returncode: %d", ex.returncode)
            logging.warning("%s exception: %s", self.get_name(), ex.output)
            if (
                self.plugin_context
                and self.plugin_context.args.clang_format_raise_exception
            ):
                return None
            return []

        for output in total_output:
            logging.debug("%s", output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
                for output in total_output:
                    fid.write(output)

        issues: list[Issue] = self.parse_tool_output(total_output, files)
        return issues

    def check_configuration(self, clang_format_bin: str) -> Optional[bool]:
        """Check that configuration is configured properly.

        Args:
            clang_format_bin: The clang-format binary.

        Returns:
            True if the configuration is correct, False otherwise.
        """
        if self.plugin_context is None:
            return False

        default_file_name = "_clang-format"
        format_file_name = self.plugin_context.resources.get_file(default_file_name)
        if not os.path.isfile(os.path.expanduser("~/" + default_file_name)):
            default_file_name = ".clang-format"
        exc_msg = (
            "_clang-format or .clang-format style is not correct. "
            f"There is one located in {format_file_name}. "
            "Put this file in your home directory."
        )
        try:
            with (
                open(
                    os.path.expanduser("~/" + default_file_name), "r", encoding="utf8"
                ) as home_format_file,
                open(
                    format_file_name, "r", encoding="utf8"  # type: ignore
                ) as format_file,
            ):
                actual_format = home_format_file.read()
                target_format = format_file.read()
            diff = difflib.context_diff(
                actual_format.splitlines(), target_format.splitlines()
            )
            for line in diff:
                if (
                    line.startswith("+ ")
                    or line.startswith("- ")
                    or line.startswith("! ")
                ) and len(line) > 2:
                    if line[2:].strip() and line[2:].strip()[0] != "#":
                        exc = subprocess.CalledProcessError(
                            -1, clang_format_bin, exc_msg
                        )
                        if self.plugin_context.args.clang_format_raise_exception:
                            raise exc

        except (IOError, OSError) as ex:
            logging.warning("%s", exc_msg)
            logging.warning("%s exception: %s", self.get_name(), ex.strerror)
            if self.plugin_context.args.clang_format_raise_exception:
                return None
            return False

        except subprocess.CalledProcessError as ex:
            logging.warning("%s Returncode = %d", exc_msg, ex.returncode)
            if self.plugin_context.args.clang_format_raise_exception:
                return None

        return True

    def parse_tool_output(  # pylint: disable=too-many-locals
        self, total_output: list[str], files: list[str]
    ) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            total_output: The output from the tool.
            files: The files to scan.

        Returns:
            A list of issues found by the tool.
        """
        clangformat_re = r"<replacement offset="
        parse: Pattern[str] = re.compile(clangformat_re)
        issues: list[Issue] = []

        if (
            not self.plugin_context
            or not self.plugin_context.args.clang_format_issue_per_line
        ):
            for output in total_output:
                lines = output.splitlines()
                filename = lines[0]
                count = 0
                for line in lines:
                    match: Optional[Match[str]] = parse.match(line)
                    if match:
                        count += 1
                if count > 0:
                    issues.append(
                        Issue(
                            filename,
                            0,
                            self.get_name(),
                            "format",
                            1,
                            str(count) + " replacements",
                            None,
                        )
                    )
        else:
            parser = ClangFormatXMLParser()
            for output, filename in zip(total_output, files):
                report = parser.parse_xml_output(output, filename)
                for issue in report:
                    msg: str = (
                        f"Replace\n{issue['deletion']}\nwith\n{issue['addition']}\n"
                    )
                    issues.append(
                        Issue(
                            filename,
                            int(issue["line_no"]),
                            self.get_name(),
                            "format",
                            1,
                            msg,
                            None,
                        )
                    )

        return issues
