"""Tool plugin."""

import argparse
import logging
import os
import re
import shlex
import subprocess
from typing import Any, Match, Optional, Pattern, Union

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext


class ToolPlugin:
    """Default implementation of tool plugin."""

    plugin_context = None
    TOOL_MISSING_STR = "Not installed"
    TOOL_UNKNOWN_STR = "Unknown"

    def get_name(self) -> str:  # type: ignore[empty-body]
        """Get name of tool.

        Returns:
            Name of tool.
        """
        pass  # pylint: disable=unnecessary-pass

    @classmethod
    def get_tool_dependencies(cls) -> list[str]:
        """Get a list of tools that must run before this one.

        Returns:
            List of tool dependencies for a tool.
        """
        return []

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments.

        Args:
            args: Flags for plugins will be added to existing arguments.
        """

    def get_file_types(self) -> list[str]:  # type: ignore[empty-body]
        """Return a list of file types the plugin can scan.

        Returns:
            List of file types the plugin can scan.
        """

    def get_binary(  # pylint: disable=unused-argument
        self, level: Optional[str] = None, package: Optional[Package] = None
    ) -> str:
        """Get tool binary name.

        Arguments are required because some tools may need to know the package or level
        to determine the binary name. The binary name can change, most often to add a
        version number as a suffix.

        Args:
            level: Level at which to run tool.
            package: Package on which to run tool.
        """
        return self.get_name()

    def get_version(self) -> str:
        """Figure out and return the version of the tool that's installed.

        If no version is found the function returns "Unknown".

        Returns:
            Version of the tool that's installed.
        """
        tool_bin = self.get_binary()
        if not tool_bin:
            return self.TOOL_UNKNOWN_STR

        try:
            output = subprocess.check_output(
                [tool_bin, "--version"], stderr=subprocess.STDOUT
            )
            return output.decode("utf-8")
        except subprocess.CalledProcessError:  # NOLINT
            return self.TOOL_UNKNOWN_STR
        except FileNotFoundError:  # NOLINT
            return self.TOOL_MISSING_STR

    def get_version_from_pkg(self, subproc_args: list[str], ver_re_str: str) -> str:
        """Figure out and return the version of the tool that's installed.

        If no version is found the function returns "Unknown".

        Args:
            subproc_args: Arguments to pass to subprocess.
            ver_re_str: Regular expression to use to parse the version from the output.

        Returns:
            Version of the tool that's installed.
        """
        version = self.TOOL_MISSING_STR

        try:
            output = subprocess.check_output(
                subproc_args,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError:  # NOLINT
            return self.TOOL_UNKNOWN_STR
        except FileNotFoundError:  # NOLINT
            return self.TOOL_UNKNOWN_STR

        parse: Pattern[str] = re.compile(ver_re_str)
        for line in output.splitlines():
            match: Optional[Match[str]] = parse.match(line)
            if match:
                return line
        return version

    def get_version_from_apt(self) -> str:
        """Figure out and return the version of the tool that's installed by apt.

        Returns:
            Version of the tool that's installed.
        """
        tool_bin = self.get_binary()
        if not tool_bin:
            return self.TOOL_UNKNOWN_STR

        return self.get_version_from_pkg(
            subproc_args=["dpkg", "-l"], ver_re_str=rf"(.+{tool_bin}.*)"
        )

    def get_version_from_docker(self) -> str:
        """Figure out and return the version of the tool that's installed by Docker.

        Returns:
            Version of the tool that's installed.
        """
        tool_bin = self.get_binary()
        if not tool_bin:
            return self.TOOL_UNKNOWN_STR

        return self.get_version_from_pkg(
            subproc_args=["docker", "image", "list"], ver_re_str=rf"(.+{tool_bin}.*)"
        )

    def get_version_from_npm(self) -> str:
        """Figure out and return the version of the tool that's installed by npm.

        Returns:
            Version of the tool that's installed.
        """
        tool_bin = self.get_binary()
        if not tool_bin:
            return self.TOOL_UNKNOWN_STR

        ver_re = rf"(.+{tool_bin}.*)@([0-9]*\.?[0-9]+\.?[0-9]+)"
        version = self.get_version_from_pkg(
            subproc_args=["npm", "list"], ver_re_str=ver_re
        )
        if version in [self.TOOL_MISSING_STR, self.TOOL_UNKNOWN_STR]:
            # if not found locally, check globally
            version = self.get_version_from_pkg(
                subproc_args=["npm", "list", "-g"], ver_re_str=ver_re
            )
        return version

    def scan(self, package: Package, level: str) -> Optional[list[Issue]]:
        """Run tool and gather output.

        Args:
            package: Package to scan.
            level: Level at which to scan.

        Returns:
            List of issues from tool.
        """
        files: list[str] = []
        for file_type in self.get_file_types():
            if file_type in package and package[file_type]:
                files += package[file_type]

        if files:
            total_output = (  # pylint: disable=assignment-from-no-return
                self.process_files(package, level, files, self.get_user_flags(level))
            )
            if total_output is not None:
                if self.plugin_context and self.plugin_context.args.output_directory:
                    with open(self.get_name() + ".log", "w", encoding="utf8") as fid:
                        for output in total_output:
                            fid.write(output)

                return self.parse_output(total_output, package)

            return None

        return []

    def process_files(
        self, package: Package, level: str, files: list[str], user_flags: list[str]
    ) -> Optional[list[str]]:
        """Run tool and gather output.

        Args:
            package: Package to scan.
            level: Level at which to scan.
            files: List of files to scan.
            user_flags: User-defined flags.

        Returns:
            List of output from tool.
        """

    def parse_output(  # type: ignore[empty-body]
        self, total_output: list[str], package: Optional[Package] = None
    ) -> list[Issue]:  # pyright: ignore
        """Parse tool output and report issues.

        Args:
            total_output: Output from tool.
            package: Package with issues.

        Returns:
            List of issues.
        """

    def set_plugin_context(self, plugin_context: Union[None, PluginContext]) -> None:
        """Set the plugin context.

        Args:
            plugin_context: Plugin context.
        """
        self.plugin_context = plugin_context

    def load_mapping(self) -> dict[str, str]:
        """Load a mapping between warnings and identifiers.

        Returns:
            Mapping between warnings and identifiers.
        """
        file_name: str = f"plugin_mapping/{self.get_name()}.txt"
        assert self.plugin_context is not None
        full_path: Union[Any, str, None] = self.plugin_context.resources.get_file(
            file_name
        )
        if (
            "mapping_file_suffix" in self.plugin_context.args
            and self.plugin_context.args.mapping_file_suffix is not None
        ):
            # If the user specified a suffix, try to get the suffixed version of the
            # file.
            suffixed_file_name = (
                f"plugin_mapping/{self.get_name()}-"
                f"{self.plugin_context.args.mapping_file_suffix}.txt"
            )
            suffixed_full_path = self.plugin_context.resources.get_file(
                suffixed_file_name
            )
            if suffixed_full_path is not None:
                # If there actually is a file with that suffix, use it.
                # Else use the un-suffixed version.
                full_path = suffixed_full_path

        if full_path is None:
            return {}
        warning_mapping: dict[str, str] = {}
        with open(full_path, "r", encoding="utf8") as mapping_file:
            for line in mapping_file.readlines():
                split_line = line.strip().split(":")
                if len(split_line) != 2:
                    logging.warning(
                        "Invalid line %s in mapping file %s", line, file_name
                    )
                    continue
                warning_mapping[split_line[0]] = split_line[1]
        return warning_mapping

    def get_user_flags(self, level: str, name: Optional[str] = None) -> list[str]:
        """Get the user-defined extra flags for a specific tool/level combination.

        Args:
            level: Level at which to scan.
            name: Name of the tool.

        Returns:
            List of user-defined flags.
        """
        if name is None:
            name = self.get_name()  # pylint: disable=assignment-from-no-return
        assert self.plugin_context is not None
        user_flags = self.plugin_context.config.get_tool_config(name, level, "flags")
        flags: list[str] = []
        if user_flags:
            # See https://github.com/python/typeshed/issues/1476 for
            # justification to ignore.
            lex = shlex.shlex(user_flags, posix=True)
            lex.whitespace_split = True
            flags = list(lex)
        return flags

    @staticmethod
    def is_valid_executable(path: str) -> bool:
        """Return whether a provided command exists and is executable.

        If the provided path has an extension on it, don't change it, otherwise try
        adding common extensions.

        Args:
            path: Path to tool binary.

        Returns:
            True if the path is a valid executable, False otherwise
        """
        # On Windows, PATHEXT contains a list of extensions which can be
        # appended to a program name when searching PATH.
        extensions = os.environ.get("PATHEXT", None)
        _, path_ext = os.path.splitext(path)
        if path_ext or not extensions:
            return os.path.isfile(path) and os.access(path, os.X_OK)

        extensions_list = extensions.split(";")
        # Add "" (no extension) as a possibility.
        extensions_list.insert(0, "")
        for ext in extensions_list:
            extended_path = path + ext
            if os.path.isfile(extended_path) and os.access(extended_path, os.X_OK):
                return True

        return False

    @staticmethod
    def command_exists(command: str) -> bool:
        """Return whether a particular command is available on $PATH.

        Args:
            command: Command to check for.

        Returns:
            True if the command is available on $PATH, False otherwise.
        """
        fpath, _ = os.path.split(command)

        if fpath:
            # Contains a path, not just a command, so don't search PATH
            return ToolPlugin.is_valid_executable(command)

        for path in os.environ["PATH"].split(os.pathsep):
            exe_path = os.path.join(path, command)
            if ToolPlugin.is_valid_executable(exe_path):
                return True

        return False
