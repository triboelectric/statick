"""Run grep."""

import logging
import re
import shlex
import subprocess

from statick_tool.issue import Issue  # pylint: disable=import-error
from statick_tool.tool_plugin import (  # pylint: disable=import-error,no-name-in-module,syntax-error
    ToolPlugin,
)


class MyCustomToolPlugin(ToolPlugin):
    """Run grep."""

    def get_name(self):
        """Get name of tool."""
        return "my_custom_tool"

    def scan(self, package, level):
        """Run tool and gather output."""
        flags = ["-rn"]
        user_flags = []
        if self.plugin_context is not None and "config" in self.plugin_context:
            user_flags = self.plugin_context.config.get_tool_config(
                self.get_name(), level, "flags"
            )
        lex = shlex.shlex(user_flags, posix=True)  # pyright: ignore
        lex.whitespace_split = True
        flags = flags + list(lex)

        output = None

        try:
            subproc_args = ["grep"] + flags + [package.path]
            output = subprocess.check_output(subproc_args, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as ex:
            logging.warning("Problem %d", ex.returncode)
            logging.warning("%s exception: %s", self.get_name(), ex.output)
            return None

        logging.debug("%s", output)

        with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
            fid.write(output)  # pyright: ignore

        issues = self.parse_output(output)
        return issues

    def parse_output(self, total_output, _=None):  # pyright: ignore
        """Parse tool output and report issues."""
        grep_re = r"(.+):(\d+):(.+)"
        parse = re.compile(grep_re)
        issues = []

        for line in total_output.split("\n"):
            match = parse.match(line)
            if match:
                issues.append(
                    Issue(
                        match.group(1),
                        int(match.group(2)),
                        self.get_name(),
                        "banned_pattern",
                        5,
                        "Banned pattern found: " + match.group(3),
                        None,
                    )
                )

        return issues
