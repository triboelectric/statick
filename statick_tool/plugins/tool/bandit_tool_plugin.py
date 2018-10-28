"""Apply bandit tool and gather results."""

from __future__ import print_function
import csv

import subprocess
import shlex

from statick_tool.tool_plugin import ToolPlugin
from statick_tool.issue import Issue


class BanditToolPlugin(ToolPlugin):
    """Apply bandit tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "bandit"

    def gather_args(self, args):
        """Gather arguments."""
        args.add_argument("--bandit-bin", dest="bandit_bin", type=str,
                          help="bandit binary path")

    def scan(self, package, level):
        """Run tool and gather output."""
        if "python_src" not in package:
            return []
        elif len(package["python_src"]) == 0:
            return []

        bandit_bin = "bandit"
        if self.plugin_context.args.bandit_bin is not None:
            bandit_bin = self.plugin_context.args.bandit_bin

        flags = ["--format=csv"]
        user_flags = self.plugin_context.config.get_tool_config(self.get_name(),
                                                                level, "flags")
        lex = shlex.shlex(user_flags, posix=True)
        lex.whitespace_split = True
        flags = flags + list(lex)

        files = []
        if "python_src" in package:
            files += package["python_src"]

        try:
            output = subprocess.check_output([bandit_bin] + flags + files,
                                             stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as ex:
            output = ex.output
            if ex.returncode != 1:
                print("bandit failed! Returncode = {}".
                      format(str(ex.returncode)))
                print("{}".format(ex.output))
                return None

        except OSError as ex:
            print("Couldn't find %s! (%s)" % (bandit_bin, ex))
            return None

        if self.plugin_context.args.show_tool_output:
            print("{}".format(output))

        with open(self.get_name() + ".log", "w") as f:
            f.write(output)

        issues = self.parse_output(output.split('\n'))
        return issues

    def parse_output(self, output):
        """Parse tool output and report issues."""
        issues = []
        # Load the plugin mapping if possible
        warnings_mapping = self.load_mapping()
        for line in output:
            line_data = line.split(',')
            if len(line_data) < 7:
                continue
            if line_data[0] == 'filename':
                # Skip the column header line
                continue
            cert_reference = None
            if line_data[1] in warnings_mapping.keys():
                cert_reference = warnings_mapping[line[1]]
            severity = '1'
            if line_data[4] == "MEDIUM":
                severity = '3'
            elif line_data[4] == "HIGH":
                severity = '5'
            issues.append(Issue(line_data[0], line_data[6],
                                self.get_name(), line_data[2],
                                severity, line_data[5], cert_reference))

        return issues
