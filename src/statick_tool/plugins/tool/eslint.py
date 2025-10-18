"""Apply eslint tool and gather results."""

import json
import logging
import pathlib
import shutil
import subprocess

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class ESLintToolPlugin(ToolPlugin):
    """Apply eslint tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "eslint"

    def get_file_types(self) -> list[str]:
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types.
        """
        return ["html_src", "javascript_src"]

    def get_format_file(self, level: str) -> tuple[str | None, bool]:
        """Retrieve format file path.

        Args:
            level: The analysis level.

        Returns:
            Tuple containing the format file path and a boolean indicating if the file was copied.
        """
        tool_config = "eslint.config.mjs"
        user_config = None
        if self.plugin_context is not None:
            user_config = self.plugin_context.config.get_tool_config(
                self.get_name(), level, "config"
            )
        if user_config is not None:
            tool_config = user_config

        install_dir = None
        if self.plugin_context is not None:
            install_dir = self.plugin_context.config.get_tool_config(
                self.get_name(), level, "install_dir"
            )
        copied_file = False
        format_file_name = None
        if install_dir is not None:
            format_file_path = pathlib.Path(install_dir, tool_config).expanduser()

            if (
                not format_file_path.exists()
                and tool_config is not None
                and self.plugin_context is not None
            ):
                file_path = self.plugin_context.resources.get_file(tool_config)
                if file_path is not None:
                    config_file_path = pathlib.Path(file_path)
                    install_dir_path = pathlib.Path(install_dir).expanduser()
                    logging.info(
                        "Copying eslint format file %s to: %s",
                        config_file_path,
                        install_dir_path,
                    )
                    shutil.copy(str(config_file_path), str(install_dir_path))
                    copied_file = True

            format_file_name = str(format_file_path)
        elif self.plugin_context is not None:
            format_file_name = self.plugin_context.resources.get_file(tool_config)

        return (format_file_name, copied_file)

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
        tool_bin = self.get_binary()

        (format_file_name, copied_file) = self.get_format_file(level)

        flags: list[str] = ["-f", "json"]
        if format_file_name is not None:
            flags += ["-c", format_file_name]
        flags += []
        flags += user_flags

        total_output: list[str] = []

        for src in files:
            try:
                exe = [tool_bin] + flags + [src]
                output = subprocess.check_output(
                    exe, stderr=subprocess.STDOUT, universal_newlines=True
                )
                total_output.append(output)

            except subprocess.CalledProcessError as ex:
                if (
                    "Error: Cannot find module" in ex.output
                    or "Require stack:" in ex.output
                ):
                    # nodejs cannot find a module and threw an error
                    # this results in the same returncode `1` that eslint
                    # uses to indicate the presence of linting issues.
                    logging.warning(
                        "%s failed! Returncode = %d", tool_bin, ex.returncode
                    )
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None

                if ex.returncode == 1:  # eslint returns 1 upon linting errors
                    total_output.append(ex.output)
                else:
                    logging.warning(
                        "%s failed! Returncode = %d", tool_bin, ex.returncode
                    )
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    if copied_file and format_file_name is not None:
                        self.remove_config_file(format_file_name)
                    return None

            except OSError as ex:
                logging.warning("Couldn't find %s! (%s)", tool_bin, ex)
                if copied_file and format_file_name is not None:
                    self.remove_config_file(format_file_name)
                return None

        if copied_file and format_file_name is not None:
            self.remove_config_file(format_file_name)

        return total_output

    # pylint: enable=too-many-locals

    @classmethod
    def remove_config_file(cls, format_file_name: str) -> None:
        """Remove config file automatically copied into directory.

        Args:
            format_file_name: The name of the format file.
        """
        format_file_path = pathlib.Path(format_file_name).expanduser()
        if format_file_path.exists():
            logging.info("Removing copied config file: %s", format_file_path)
            format_file_path.unlink()

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
        for output in total_output:
            try:
                data = json.loads(output)
                for line in data:
                    file_path = line["filePath"]
                    for issue in line["messages"]:
                        severity_str = issue["severity"]
                        severity = 3
                        if severity_str == 1:  # warning
                            severity = 3
                        elif severity_str == 2:  # error
                            severity = 5
                        line_num = 0
                        if "line" in issue:
                            line_num = issue["line"]
                        issues.append(
                            Issue(
                                file_path,
                                line_num,
                                self.get_name(),
                                issue["ruleId"],
                                severity,
                                issue["message"],
                                None,
                            )
                        )

            except json.JSONDecodeError as ex:
                logging.warning("JSONDecodeError: %s", ex)
            except ValueError as ex:
                logging.warning("ValueError: %s", ex)

        return issues
