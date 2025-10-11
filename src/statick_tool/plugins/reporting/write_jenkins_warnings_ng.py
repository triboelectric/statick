"""Write Statick results to Jenkins Warnings-NG plugin json-log compatible output."""

import json
import logging
import os

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.reporting_plugin import ReportingPlugin


class WriteJenkinsWarningsNGReportingPlugin(ReportingPlugin):
    """Writes Statick results to Jenkins Warnings-NG json-log compatible output."""

    def get_name(self) -> str:
        """Return the plugin name."""
        return "write_jenkins_warnings_ng"

    def report(
        self, package: Package, issues: dict[str, list[Issue]], level: str
    ) -> tuple[None, bool]:
        """Write the results to Jenkins Warnings-NG plugin compatible file.

        Args:
            package: The Package object that was analyzed.
            issues: The issues found by the Statick analysis, keyed by the tool that found them.
            level: Name of the level used in the scan.

        Returns:
            None, True if the report was successfully written, otherwise None, False.
        """
        if self.plugin_context is None:
            return None, False

        # Do not write report to file if no output directory is given.
        if not self.plugin_context.args.output_directory:
            return None, True

        # We _should_ be in output_dir already, but let's be safe about it.
        output_dir = os.path.join(
            self.plugin_context.args.output_directory, package.name + "-" + level
        )

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        if not os.path.isdir(output_dir):
            logging.error("Unable to create output directory at %s!", output_dir)
            return None, False

        output_file = os.path.join(
            output_dir, package.name + "-" + level + ".json.statick"
        )
        next_output_file = os.path.join(
            output_dir, package.name + "-" + level + ".jenkins-ng.json"
        )
        logging.warning(
            "Output filename will change in statick v0.9.0 from %s to %s",
            output_file,
            next_output_file,
        )
        logging.info("Writing output to %s", output_file)
        with open(output_file, "w", encoding="utf8") as out:
            for _, value in issues.items():
                for issue in value:
                    severity = "LOW"
                    try:
                        if int(issue.severity) > 0:
                            severity = "NORMAL"
                        if int(issue.severity) > 2:
                            severity = "HIGH"
                        if int(issue.severity) > 4:
                            severity = "ERROR"
                    except ValueError as ex:
                        logging.warning(
                            "Invalid severity integer (%s), using default 'LOW' "
                            " severity. Error = %s",
                            issue.severity,
                            ex,
                        )
                    issue_dict = {
                        "fileName": issue.filename,
                        "severity": severity,
                        "lineStart": issue.line_number,
                        "message": issue.message,
                        "category": issue.tool,
                        "type": issue.issue_type,
                    }
                    line = json.dumps(issue_dict, sort_keys=True) + "\n"
                    out.write(line)

        return None, True
