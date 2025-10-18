"""Apply uncrustify tool and gather results."""

import argparse
import difflib
import logging
import subprocess

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class UncrustifyToolPlugin(ToolPlugin):
    """Apply uncrustify tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "uncrustify"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments.

        Args:
            args: Flags for this plugin will be added to these existing arguments.
        """
        args.add_argument(
            "--uncrustify-bin",
            dest="uncrustify_bin",
            type=str,
            help="uncrustify binary path",
        )

    def get_binary(  # pylint: disable=unused-argument
        self, level: str | None = None, package: Package | None = None
    ) -> str:
        """Get tool binary name.

        Args:
            level: The level to process (optional).
            package: The package to process (optional).

        Returns:
            Name of the tool binary.
        """
        binary = self.get_name()
        if (
            self.plugin_context is not None
            and self.plugin_context.args.uncrustify_bin is not None
        ):
            binary = self.plugin_context.args.uncrustify_bin

        return binary

    def scan(  # pylint: disable=too-many-locals, too-many-branches
        self, package: Package, level: str
    ) -> list[Issue] | None:
        """Run tool and gather output.

        Args:
            package: The package to process.
            level: The level to process.

        Returns:
            List of issues or None.
        """
        if "make_targets" not in package and "headers" not in package:
            return []

        if self.plugin_context is None:
            return None

        uncrustify_bin = self.get_binary()

        flags: list[str] = []
        flags += self.get_user_flags(level)

        files: list[str] = []
        if "make_targets" in package:
            for target in package["make_targets"]:
                files += target["src"]
        if "headers" in package:
            files += package["headers"]

        total_output: list[str] = []

        try:
            format_file_name = self.plugin_context.resources.get_file("uncrustify.cfg")

            for src in files:
                cmd = [uncrustify_bin, "-c", format_file_name, "-f", src]
                output = subprocess.check_output(
                    cmd,  # type: ignore
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                )
                src_cmd = ["cat", src]
                src_output = subprocess.check_output(
                    src_cmd, stderr=subprocess.STDOUT, universal_newlines=True
                )
                diff = difflib.context_diff(
                    output.splitlines(), src_output.splitlines()
                )
                found_diff = False
                output = output.split("\n", 1)[1]
                for line in diff:
                    if (
                        line.startswith("---")
                        or line.startswith("***")
                        or line.startswith("! Parsing")
                        or src in line
                        or line.isspace()
                    ):
                        continue
                    # This is a bug I can't figure out yet.
                    if "#ifndef" in line or "#define" in line:
                        continue
                    found_diff = True
                if found_diff:
                    total_output.append(src)

        except subprocess.CalledProcessError as ex:
            output = ex.output
            logging.warning("uncrustify failed! Returncode = %d", ex.returncode)
            logging.warning("%s exception: %s", self.get_name(), ex.output)
            return None

        except OSError as ex:
            logging.warning("Couldn't find uncrustify executable! (%s)", ex)
            return None

        for output in total_output:
            logging.debug("%s", output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
                for output in total_output:
                    fid.write(output)

        issues: list[Issue] = self.parse_output(total_output, package)
        return issues

    def parse_output(
        self, total_output: list[str], package: Package | None = None
    ) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            total_output: List of output strings.
            package: The package to process (optional).

        Returns:
            List of issues.
        """
        issues: list[Issue] = []
        for output in total_output:
            issues.append(
                Issue(
                    output,
                    0,
                    self.get_name(),
                    "format",
                    1,
                    "Uncrustify mis-match",
                    None,
                )
            )

        return issues
