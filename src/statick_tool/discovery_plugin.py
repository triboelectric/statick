"""Discovery plugin."""

import logging
import os
import subprocess
import sys
from typing import Any

from statick_tool.exceptions import Exceptions
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext


class DiscoveryPlugin:
    """Default implementation of discovery plugin."""

    plugin_context = None

    def get_name(self) -> str | None:
        """Get name of plugin.

        Returns:
            Name of plugin.
        """

    @classmethod
    def get_discovery_dependencies(cls) -> list[str]:
        """Get a list of discovery plugins that must run before this one.

        Returns:
            List of discovery plugin names.
        """
        return []

    def gather_args(self, args: Any) -> None:
        """Gather arguments for plugin.

        Args:
            args: Flags for plugins will be added to existing arguments.
        """

    def scan(
        self, package: Package, level: str, exceptions: Exceptions | None = None
    ) -> None:
        """Scan package to discover files for analysis.

        If exceptions is passed, then the plugin should (if practical) use it to filter
        which files the plugin detects.

        Args:
            package: Package to scan.
            level: Level at which to scan.
            exceptions: Exceptions to apply to discovery.
        """

    def find_files(self, package: Package) -> None:
        """Walk the package path exactly once to discover files for analysis.

        Args:
            package: Package to scan.
        """
        if package._walked:  # pylint: disable=protected-access
            return

        for root, _, files in os.walk(package.path):
            for fname in files:
                full_path = os.path.join(root, fname)
                abs_path = os.path.abspath(full_path)
                file_output = self.get_file_cmd_output(full_path)
                file_dict = {
                    "name": fname.lower(),
                    "path": abs_path,
                    "file_cmd_out": file_output,
                }
                package.files[abs_path] = file_dict

        package._walked = True  # pylint: disable=protected-access

    def get_file_cmd_output(self, full_path: str) -> str:
        """Run the file command (if it exists) on the supplied path.

        The output from the file command is converted to lowercase.
        There are two recommended ways to check it:
        1. When searching for a single string just use the python "in" operator:

            if "search string" in file_dict["file_cmd_out"]:

        2. When searching for multiple different strings, use the `any()` function:

            expected_output = ("output_1", "output_2")
            if any(item in file_dict["file_cmd_out"] for item in expected_output):

        Args:
            full_path: Full path to file.

        Returns:
            Output of file command.
        """
        if not self.file_command_exists():
            return ""

        try:
            output: str = subprocess.check_output(
                ["file", full_path], universal_newlines=True
            )
            return output.lower()
        except subprocess.CalledProcessError as ex:
            logging.warning(
                "Failed to run 'file' command. Returncode = %d", ex.returncode
            )
            logging.warning("Exception output: %s", ex.output)
            return ""
        except OSError:
            logging.warning("OSError on file command for %s", full_path)
            return ""

    def set_plugin_context(self, plugin_context: None | PluginContext) -> None:
        """Set the plugin context.

        Args:
            plugin_context: The plugin context.
        """
        self.plugin_context = plugin_context

    @staticmethod
    def file_command_exists() -> bool:
        """Return whether the 'file' command is available on $PATH.

        Returns:
            True if the 'file' command is available on $PATH, False otherwise.
        """
        if sys.platform == "win32":
            command_name = "file.exe"
        else:
            command_name = "file"

        for path in os.environ["PATH"].split(os.pathsep):
            exe_path = os.path.join(path, command_name)
            if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
                return True

        return False
