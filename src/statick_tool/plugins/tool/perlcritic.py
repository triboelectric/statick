"""Apply Perl::Critic tool and gather results."""

import argparse
import logging
import subprocess

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class PerlCriticToolPlugin(ToolPlugin):
    """Apply Perl::Critic tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            The name of the tool.
        """
        return "perlcritic"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments.

        Args:
            args: Flags for this plugin will be added to these existing arguments.
        """
        args.add_argument(
            "--perlcritic-bin",
            dest="perlcritic_bin",
            type=str,
            help="perlcritic binary path",
        )

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            A list of file types.
        """
        return ["perl_src"]

    def get_binary(  # pylint: disable=unused-argument
        self, level: str | None = None, package: Package | None = None
    ) -> str:
        """Get tool binary name.

        Args:
            level: The level of the scan.
            package: The package to scan.

        Returns:
            The binary name of the tool.
        """
        binary = self.get_name()
        if self.plugin_context and self.plugin_context.args.perlcritic_bin is not None:
            binary = self.plugin_context.args.perlcritic_bin
        return binary

    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> list[str] | None:
        """Run tool and gather output.

        Args:
            package: The package to scan.
            level: The level of the scan.
            files: The files to scan.
            user_flags: The user flags to pass to the tool.

        Returns:
            The output from the tool.
        """
        flags = ["--nocolor", "--verbose=%f:::%l:::%p:::%m:::%s\n"]
        flags += self.get_user_flags(level)

        perlcritic_bin = self.get_binary()

        try:
            output = subprocess.check_output(
                [perlcritic_bin] + flags + files,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            ).join(" ")

        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 2:
                logging.warning("perlcritic failed! Returncode = %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return []

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", perlcritic_bin, ex)
            return []

        logging.debug("%s", output)
        return output.splitlines()

    def parse_output(
        self, total_output: list[str], package: Package | None = None
    ) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            total_output: The output from the tool.
            package: The package to scan.

        Returns:
            A list of issues parsed from the output.
        """
        issues: list[Issue] = []
        # Load the plugin mapping if possible
        warnings_mapping = self.load_mapping()
        for line in total_output:
            split_line = line.strip().split(":::")
            # Should split into five segments, anything less is invalid.
            if len(split_line) < 5:
                continue
            cert_reference = None
            if split_line[2].replace("::", "__") in warnings_mapping:
                cert_reference = warnings_mapping[split_line[2].replace("::", "__")]

            issues.append(
                Issue(
                    split_line[0],
                    int(split_line[1]),
                    self.get_name(),
                    split_line[2],
                    int(split_line[4]),
                    split_line[3],
                    cert_reference,
                )
            )

        return issues
