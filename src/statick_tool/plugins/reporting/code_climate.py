"""Prints the Statick reports out to the terminal or file in Code Climate JSON."""

import hashlib
import json
import logging
import os
from collections import OrderedDict
from typing import Any

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.reporting_plugin import ReportingPlugin


class CodeClimateReportingPlugin(ReportingPlugin):
    """Prints the Statick reports out to the terminal or file in Code Climate JSON."""

    def get_name(self) -> str:
        """Return the plugin name."""
        return "code_climate"

    def report(
        self, package: Package, issues: dict[str, list[Issue]], level: str
    ) -> tuple[None, bool]:
        """Go through the issues list and print them in JSON format.

        Args:
            package: The Package object that was analyzed.
            issues: The issues found by the Statick analysis, keyed by the tool that found them.
            level: Name of the level used in the scan.

        Returns:
            None, True if the report was successfully printed, otherwise None, False.
        """
        if not self.plugin_context or not self.plugin_context.config:
            return None, False

        file_output = self.plugin_context.config.str_to_bool(
            self.plugin_context.config.get_reporting_config(
                self.get_name(), level, "files"
            )
        )
        terminal_output = self.plugin_context.config.str_to_bool(
            self.plugin_context.config.get_reporting_config(
                self.get_name(), level, "terminal"
            )
        )
        gitlab = self.plugin_context.config.str_to_bool(
            self.plugin_context.config.get_reporting_config(
                self.get_name(), level, "gitlab"
            )
        )

        # Load the plugin mapping if possible
        category_mapping = self.load_mapping()

        all_issues = []
        for _, value in issues.items():
            for issue in value:
                all_issues.append(self.get_issue_dict(issue, category_mapping, gitlab))
        line = json.dumps(all_issues)

        if file_output:
            if not self.write_output(package, level, line):
                return None, False

        if terminal_output:
            print(line)

        return None, True

    @classmethod
    def get_issue_dict(
        cls, issue: Issue, category_mapping: dict[str, str], gitlab: bool
    ) -> dict[str, Any]:
        """Convert Issue object into dictionary.

        Args:
            issue: The Issue object to convert.
            category_mapping: A dictionary mapping issue categories.
            gitlab: A boolean indicating if the output is for GitLab.

        Returns:
            A dictionary representation of the issue.
        """
        severity = "info"
        try:
            if int(issue.severity) > 0:
                severity = "minor"
            if int(issue.severity) > 2:
                severity = "major"
            if int(issue.severity) > 4:
                severity = "critical"
        except ValueError as ex:
            logging.warning(
                "Invalid severity integer (%s), using default 'info' "
                " severity. Error = %s",
                issue.severity,
                ex,
            )
        issue_dict: dict[str, Any] = OrderedDict()

        issue_dict["severity"] = severity

        categories = set()
        if issue.tool in category_mapping:
            categories.add(category_mapping[issue.tool])
        if issue.issue_type in category_mapping:
            categories.add(category_mapping[issue.issue_type])

        # gitlab only uses the description field, so including issue.tool here too
        description = issue.tool + ": " + issue.issue_type + ": " + issue.message
        if issue.cert_reference:
            description += ", CERT Reference: " + issue.cert_reference
            categories.add("Security")
        issue_dict["description"] = description

        issue_dict["location"] = OrderedDict()
        issue_dict["location"]["path"] = issue.filename
        issue_dict["location"]["lines"] = OrderedDict()
        issue_dict["location"]["lines"]["begin"] = issue.line_number

        # Exclude fields not used by gitlab if the report is too large (>10MB)
        # https://docs.gitlab.com/ee/user/project/merge_requests/code_quality.html#no-code-quality-report-is-displayed-in-a-merge-request
        if not gitlab:
            issue_dict["type"] = "issue"
            issue_dict["check_name"] = issue.tool
            issue_dict["categories"] = list(categories)

        fingerprint = hashlib.md5(json.dumps(issue_dict).encode())
        issue_dict["fingerprint"] = fingerprint.hexdigest()
        return issue_dict

    def write_output(self, package: Package, level: str, line: str) -> bool:
        """Write JSON output to a file.

        Args:
            package: The Package object that was analyzed.
            level: Name of the level used in the scan.
            line: The JSON string to write to the file.

        Returns:
            True if the output was successfully written, otherwise False.
        """
        # By default write report to the current directory.
        output_dir = os.getcwd()
        if (
            self.plugin_context
            and "output_directory" in self.plugin_context.args
            and self.plugin_context.args.output_directory is not None
        ):
            # If an output directory is specified use it for the report.
            output_dir = os.path.join(
                self.plugin_context.args.output_directory, package.name + "-" + level
            )

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        if not os.path.isdir(output_dir):
            logging.error("Unable to create output directory at %s!", output_dir)
            return False
        output_file = os.path.join(
            output_dir, package.name + "-" + level + ".code-climate.json"
        )
        logging.info("Writing output to %s", output_file)
        with open(output_file, "w", encoding="utf8") as out:
            out.write(line)

        return True
