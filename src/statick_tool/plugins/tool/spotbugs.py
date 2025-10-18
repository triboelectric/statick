"""Apply spotbugs tool and gather results."""

import logging
import os
import subprocess
import xml.etree.ElementTree as etree

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class SpotbugsToolPlugin(ToolPlugin):
    """Apply spotbugs tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "spotbugs"

    @classmethod
    def get_tool_dependencies(cls) -> list[str]:
        """Get a list of tools that must run before this one.

        Returns:
            List of tool dependencies.
        """
        return ["make"]

    def scan(self, package: Package, level: str) -> list[Issue] | None:
        """Run tool and gather output.

        Args:
            package: The package to process.
            level: The level to process.

        Returns:
            List of issues or None.
        """
        # Sanity check - make sure mvn exists
        if not self.command_exists("mvn"):
            logging.warning(
                "Couldn't find 'mvn' command, can't run Spotbugs Maven integration"
            )
            return None

        if self.plugin_context is None:
            return None

        flags: list[str] = [
            "-Dspotbugs.effort=Max",
            "-Dspotbugs.threshold=Low",
            "-Dspotbugs.xmlOutput=true",
        ]
        flags += self.get_user_flags(level)

        include_file: str | None = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "include"
        )
        exclude_file: str | None = self.plugin_context.config.get_tool_config(
            self.get_name(), level, "exclude"
        )
        if include_file is not None:
            include_file_path = self.plugin_context.resources.get_file(include_file)
            flags += [f"-Dspotbugs.includeFilterFile={include_file_path}"]

        if exclude_file is not None:
            exclude_file_path = self.plugin_context.resources.get_file(exclude_file)
            flags += [f"-Dspotbugs.excludeFilterFile={exclude_file_path}"]

        issues: list[Issue] = []
        total_output: str = ""
        for pom in package["top_poms"]:
            try:
                # The spotbugs:spotbugs-maven-plugin split is auto-concatenated
                output = subprocess.check_output(
                    ["mvn", "com.github.spotbugs:spotbugs-maven-plugin:spotbugs"]
                    + flags,
                    cwd=os.path.dirname(pom),
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                )
            except subprocess.CalledProcessError as ex:
                output = ex.output
                logging.warning("spotbugs failed! Returncode = %d", ex.returncode)
                logging.warning("%s exception: %s", self.get_name(), ex.output)
                return None

            except OSError as ex:
                logging.warning("Couldn't find maven! (%s)", ex)
                return None

            logging.debug("%s", output)
            total_output += output

        # The results will be output to (pom path)/target/spotbugs.xml for each pom
        for pom in package["all_poms"]:
            if os.path.exists(
                os.path.join(os.path.dirname(pom), "target", "spotbugs.xml")
            ):
                with open(
                    os.path.join(os.path.dirname(pom), "target", "spotbugs.xml"),
                    encoding="utf8",
                ) as outfile:
                    issues += self.parse_file_output(outfile.read())  # type: ignore

        return issues

    def parse_file_output(  # pylint: disable=too-many-locals
        self, output: str
    ) -> list[Issue] | None:
        """Parse tool output and report issues.

        Args:
            output: Output string.

        Returns:
            List of issues or None.
        """
        issues: list[Issue] = []
        # Load the plugin mapping if possible
        warnings_mapping = self.load_mapping()
        try:
            output_xml = etree.fromstring(output)
        except etree.ParseError as ex:
            logging.warning(
                "Couldn't parse Spotbugs output (%s)! Provided output was:\n%s",
                ex,
                output,
            )
            return None  # This might be better to return empty issues list here.
        for file_entry in output_xml.findall("file"):
            # Generate the filename
            file_base = file_entry.attrib["classname"].replace(".", os.sep)
            java_path_string = f"{file_base}.java"
            file_path = ""
            for source_dir in output_xml.findall("Project/SrcDir"):
                if source_dir.text is not None:
                    norm_src_path = os.path.normpath(source_dir.text)
                    joined_path = os.path.join(norm_src_path, java_path_string)
                    if os.path.exists(joined_path):
                        file_path = joined_path
                        break
            if not file_path:
                logging.warning(
                    "Couldn't find file for class %s", file_entry.attrib["classname"]
                )
                file_path = java_path_string
            for issue in file_entry.findall("BugInstance"):
                severity = 1
                if issue.attrib["priority"] == "Normal":
                    severity = 3
                elif issue.attrib["priority"] == "High":
                    severity = 5

                cert_reference = None
                if issue.attrib["type"] in warnings_mapping:
                    cert_reference = warnings_mapping[issue.attrib["type"]]
                issues.append(
                    Issue(
                        file_path,
                        int(issue.attrib["lineNumber"]),
                        self.get_name(),
                        issue.attrib["type"],
                        severity,
                        issue.attrib["message"],
                        cert_reference,
                    )
                )
        return issues
