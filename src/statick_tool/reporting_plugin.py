"""Result reporting plugin."""

import argparse
import logging
from typing import Any, Optional, Tuple, Union

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext


class ReportingPlugin:
    """Default implementation of reporting plugin."""

    plugin_context = None

    def get_name(self) -> Optional[str]:
        """Get name of reporting plugin.

        Returns:
            Name of reporting plugin.
        """

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments.

        Args:
            args: Flags for plugins will be added to existing arguments.
        """

    def report(  # type: ignore[empty-body]
        self, package: Package, issues: dict[str, list[Issue]], level: str
    ) -> Tuple[Optional[None], bool]:  # pyright: ignore
        """Run the report generator.

        Args:
            package: Package with issues.
            issues: Issues to report.
            level: Level at which to report.

        Returns:
            Tuple of None and False.
        """

    def set_plugin_context(self, plugin_context: Union[None, PluginContext]) -> None:
        """Setter for plugin_context.

        Args:
            plugin_context: Plugin context.
        """
        self.plugin_context = plugin_context

    def load_mapping(self) -> dict[str, str]:
        """Load a mapping between two sets.

        Returns:
            Mapping between two sets for issues and specific warning types. An example
            is SEI CERT C++ warnings found by supported tools.
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
