"""Apply hadolint tool and gather results."""

import argparse
import json
import logging
import subprocess

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class HadolintToolPlugin(ToolPlugin):
    """Apply hadolint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "hadolint"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments.

        Args:
            args: Flags for this plugin will be added to these existing arguments.
        """
        args.add_argument(
            "--hadolint-bin",
            dest="hadolint_bin",
            type=str,
            help="hadolint binary path",
        )
        args.add_argument(
            "--hadolint-docker",
            dest="hadolint_docker",
            action="store_true",
            help="Use hadolint docker image instead of binary",
        )

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return ["dockerfile_src"]

    def get_binary(  # pylint: disable=unused-argument
        self, level: str | None = None, package: Package | None = None
    ) -> str:
        """Get tool binary name.

        Args:
            level: The analysis level.
            package: The package being analyzed.

        Returns:
            Name of the tool binary.
        """
        binary = self.get_name()
        # If the user explicitly specifies a binary, let that override the default
        if self.plugin_context and self.plugin_context.args.hadolint_bin is not None:
            binary = self.plugin_context.args.hadolint_bin
        return binary

    def get_version(self) -> str:
        """Figure out and return the version of the tool that's installed.

        Returns:
            Version of the tool or "Unknown" if not found.
        """
        if (
            self.plugin_context
            and self.plugin_context.args.hadolint_docker is not None
            and self.plugin_context.args.hadolint_docker
        ):
            return self.get_version_from_docker()

        version = super().get_version()
        if version in [ToolPlugin.TOOL_MISSING_STR, ToolPlugin.TOOL_UNKNOWN_STR]:
            version = self.get_version_from_docker()
        return version

    # pylint: disable=too-many-locals
    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> list[str] | None:
        """Run tool and gather output.

        Args:
            package: The package being analyzed.
            level: The analysis level.
            files: List of files to process.
            user_flags: List of user flags.

        Returns:
            List of output strings or None.
        """
        tool_config = ".hadolint.yaml"
        user_config = None
        if self.plugin_context is not None:
            user_config = self.plugin_context.config.get_tool_config(
                self.get_name(), level, "config"
            )
        if user_config is not None:
            tool_config = user_config

        config_file_path = None
        if self.plugin_context is not None:
            config_file_path = self.plugin_context.resources.get_file(tool_config)
        flags: list[str] = ["-f", "json", "--no-fail"]
        if "-f" in user_flags:
            idx = user_flags.index("-f")
            logging.warning(
                "Statick requires hadolint to output in json format, "
                "ignoring user provided format: %s",
                user_flags[idx + 1],
            )
            user_flags.pop(idx)
            user_flags.pop(idx)
        flags += user_flags

        tool_bin = self.get_binary()

        total_output: list[str] = []
        if (
            self.plugin_context
            and self.plugin_context.args.hadolint_docker is not None
            and self.plugin_context.args.hadolint_docker
            and config_file_path is not None
        ):
            output = self.scan_docker(tool_bin, flags, files, config_file_path)
        else:
            if config_file_path is not None and config_file_path:
                flags += ["-c", config_file_path]
            output = self.scan_local_binary(tool_bin, flags, files)

        if output:
            total_output.append(output)
        else:
            return None

        for output in total_output:
            logging.debug("%s", output)

        return total_output

    # pylint: enable=too-many-locals

    def scan_local_binary(
        self, tool_bin: str, flags: list[str], files: list[str]
    ) -> str | None:
        """Use locally installed hadolint binary to scan.

        Args:
            tool_bin: The tool binary.
            flags: List of flags.
            files: List of files to scan.

        Returns:
            Output string or None.
        """
        try:
            exe = [tool_bin] + flags
            exe.extend(files)
            output = subprocess.check_output(
                exe, stderr=subprocess.STDOUT, universal_newlines=True
            )
            return output

        except subprocess.CalledProcessError as ex:
            logging.warning("%s failed! Returncode = %d", tool_bin, ex.returncode)
            logging.warning("%s exception: %s", self.get_name(), ex.output)
            return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
            return None

    def scan_docker(
        self, tool_bin: str, flags: list[str], files: list[str], config_file_path: str
    ) -> str | None:
        """Use hadolint docker image to scan.

        Args:
            tool_bin: The tool binary.
            flags: List of flags.
            files: List of files to scan.
            config_file_path: Path to the config file.

        Returns:
            Output string or None.
        """
        try:
            json_dict = []
            for src in files:
                exe = [
                    "docker",
                    "run",
                    "--rm",
                    "-i",
                ]
                if config_file_path is not None and config_file_path:
                    exe.extend(
                        [
                            "-v",
                            config_file_path + ":/.config/hadolint.yaml",
                        ]
                    )
                exe.extend(
                    [
                        "-v",
                        src + ":/Dockerfile",
                        "hadolint/hadolint",
                        "hadolint",
                    ]
                )
                exe.extend(flags)
                exe.append("Dockerfile")
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                if output:
                    output = output.replace(
                        '"file":"Dockerfile"', '"file":"' + src + '"'
                    )
                    try:
                        file_dict = json.loads(output)
                        for issue in file_dict:
                            json_dict.append(issue)
                    except json.decoder.JSONDecodeError as ex:
                        logging.error("Failed to decode json from %s, %s", output, ex)
                        return None
            return json.dumps(json_dict)

        except subprocess.CalledProcessError as ex:
            logging.warning("%s failed! Returncode = %d", tool_bin, ex.returncode)
            logging.warning("%s exception: %s", self.get_name(), ex.output)
            return None

        except OSError as ex:
            logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
            return None

    def parse_output(
        self, total_output: list[str], package: Package | None = None
    ) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            total_output: List of output strings.
            package: The package being analyzed.

        Returns:
            List of issues.
        """
        issues: list[Issue] = []

        # pylint: disable=too-many-nested-blocks
        for output in total_output:
            for line in output.splitlines():
                if line:
                    try:
                        err_arr = json.loads(line)
                        for issue in err_arr:
                            severity_str = issue["level"]
                            severity = 1
                            if severity_str == "style":
                                severity = 1
                            elif severity_str == "info":
                                severity = 1
                            elif severity_str == "warning":
                                severity = 3
                            elif severity_str == "error":
                                severity = 5
                            issues.append(
                                Issue(
                                    issue["file"],
                                    int(issue["line"]),
                                    self.get_name(),
                                    issue["code"],
                                    severity,
                                    issue["message"],
                                    None,
                                )
                            )

                    except ValueError as ex:
                        logging.warning("ValueError: %s, line: %s", ex, line)
        # pylint: enable=too-many-nested-blocks
        return issues
