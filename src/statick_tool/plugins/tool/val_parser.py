"""Apply VAL Parser tool and gather results.

Tool is from King's College London. Tool authors are:

- Maria Fox and Derek Long - PDDL2.2 and VAL
- Richard Howey - PDDL2.2 and VAL and Continuous Effects, derived predicates,
  timed initial literals and LaTeX report in VAL
- Stephen Cresswell - PDDL2.2 Parser

https://github.com/KCL-Planning/VAL/tree/master/applications#parser
"""

import argparse
import logging
import re
import subprocess
from typing import Match, Pattern

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ValParserToolPlugin(ToolPlugin):
    """Apply Parser tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "val_parser"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments.

        Args:
            args: Flags for this plugin will be added to these existing arguments.
        """
        args.add_argument(
            "--val-parser-bin",
            dest="val_parser_bin",
            type=str,
            help="VAL Parser binary path",
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
        binary = "Parser"
        if (
            self.plugin_context is not None
            and self.plugin_context.args.val_parser_bin is not None
        ):
            binary = self.plugin_context.args.val_parser_bin
        return binary

    def scan(self, package: Package, level: str) -> list[Issue] | None:
        """Run tool and gather output.

        Args:
            package: The package to process.
            level: The level to process.

        Returns:
            List of issues or None.
        """
        if "pddl_domain_src" not in package or not package["pddl_domain_src"]:
            return []

        flags: list[str] = []
        flags += self.get_user_flags(level)

        parser_bin = self.get_binary()

        try:
            subproc_args: list[str] = (
                [parser_bin]
                + flags
                + package["pddl_domain_src"]
                + package["pddl_problem_src"]
            )
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )

        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 255:
                logging.warning("VAL Parser failed! Returncode = %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", parser_bin, ex)
            return None

        logging.debug("%s", output)

        if self.plugin_context and self.plugin_context.args.output_directory:
            with open(self.get_name() + ".log", "w", encoding="utf-8") as fid:
                fid.write(output)

        issues: list[Issue] = self.parse_tool_output(output)
        return issues

    def parse_tool_output(self, output: str) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            output: Output string.

        Returns:
            List of issues.
        """
        tool_re: str = r"(.+):\s(.+):\s(.+):\s(.+):\s(.+)\s(.+)"
        parse: Pattern[str] = re.compile(tool_re)
        issues: list[Issue] = []
        issue_found = False

        for line in output.splitlines():
            # If we find this pattern then all following lines will have an issue per
            # line. That's when we start parsing.
            if line.startswith("Errors:") and "warnings:" in line:
                issue_found = True
                continue

            if issue_found:
                match: Match[str] | None = parse.match(line)
                if match:
                    severity = 1
                    if match.group(4) == "Warning":
                        severity = 3
                    elif match.group(4) == "Error":
                        severity = 5

                    issue = Issue(
                        match.group(1),
                        int(match.group(3)),
                        self.get_name(),
                        "PDDL",
                        severity,
                        match.group(5) + " " + match.group(6),
                        None,
                    )

                    issues.append(issue)

        return issues
