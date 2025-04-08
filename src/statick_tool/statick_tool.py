"""Code analysis front-end."""

import argparse
import copy
import io
import logging
import multiprocessing
import os
import sys
import time
from importlib.metadata import version
from logging.handlers import MemoryHandler
from typing import Any, Optional, Tuple

from statick_tool.config import Config
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.profile import Profile
from statick_tool.resources import Resources
from statick_tool.timing import Timing
from statick_tool.tool_version import ToolVersion

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


class Statick:  # pylint: disable=too-many-instance-attributes
    """Code analysis front-end."""

    def __init__(self, user_paths: list[str]) -> None:
        """Initialize Statick.

        Args:
            user_paths: List of paths to search for resource files.
        """
        self.default_level = "default"
        self.resources = Resources(user_paths)

        self.discovery_plugins: dict[str, Any] = {}
        plugins = entry_points(group="statick_tool.plugins.discovery")
        for plugin_type in plugins:
            plugin = plugin_type.load()
            self.discovery_plugins[plugin_type.name] = plugin()

        self.reporting_plugins: dict[str, Any] = {}
        plugins = entry_points(group="statick_tool.plugins.reporting")
        for plugin_type in plugins:
            plugin = plugin_type.load()
            self.reporting_plugins[plugin_type.name] = plugin()

        self.tool_plugins: dict[str, Any] = {}
        plugins = entry_points(group="statick_tool.plugins.tool")
        for plugin_type in plugins:
            plugin = plugin_type.load()
            self.tool_plugins[plugin_type.name] = plugin()

        self.config: Optional[Config] = None
        self.exceptions: Optional[Exceptions] = None
        self.timings: list[Timing] = []
        self.tool_versions: list[ToolVersion] = []

    @staticmethod
    def set_logging_level(args: argparse.Namespace) -> None:
        """Set the logging level to use for output.

        Valid levels are: DEBUG, INFO, WARNING, ERROR, CRITICAL. Specifying the level is
        case-insensitive (both upper-case and lower-case are allowed).

        Args:
            args: Arguments from command line.
        """
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = args.log_level.upper()
        if log_level not in valid_levels:
            log_level = "WARNING"
        args.log_level = log_level
        logging.basicConfig(level=log_level)
        logging.root.setLevel(log_level)
        logging.info("Log level set to %s", args.log_level.upper())

    @classmethod
    def set_cpu_count(cls, num_cpus: str) -> int:
        """Set correct number of CPU cores to use.

        Args:
            num_cpus: Desired number of CPU cores to use.

        Returns:
            Number of CPU cores to actually use.
        """
        max_cpus = multiprocessing.cpu_count()
        desired = int(num_cpus)
        if desired > max_cpus or desired == -1:
            return max_cpus
        if desired > 1:
            return desired

        return 1

    def get_config(self, args: argparse.Namespace) -> None:
        """Get Statick configuration.

        Args:
            args: Arguments from command line.
        """
        base_config_filename = "config.yaml"
        user_config_filename = ""
        if args.config is not None:
            user_config_filename = args.config
        try:
            self.config = Config(
                self.resources.get_file(base_config_filename),
                self.resources.get_file(user_config_filename),
                self.default_level,
            )
        except OSError as ex:
            logging.error(
                "Failed to access configuration file %s or %s: %s",
                base_config_filename,
                user_config_filename,
                ex,
            )
        except ValueError as ex:
            logging.error(
                "Configuration file %s or %s has errors: %s",
                base_config_filename,
                user_config_filename,
                ex,
            )

    def get_exceptions(self, args: argparse.Namespace) -> None:
        """Get Statick exceptions.

        Args:
            args: Arguments from command line.
        """
        exceptions_filename = "exceptions.yaml"
        if args.exceptions is not None:
            exceptions_filename = args.exceptions
        try:
            self.exceptions = Exceptions(self.resources.get_file(exceptions_filename))
        except OSError as ex:
            logging.error(
                "Failed to access exceptions file %s: %s", exceptions_filename, ex
            )
        except ValueError as ex:
            logging.error("Exceptions file %s has errors: %s", exceptions_filename, ex)

    def get_ignore_packages(self) -> list[str]:
        """Get packages to ignore during scan process.

        Returns:
            Packages to skip when scanning.
        """
        if self.exceptions is None:
            return []
        return self.exceptions.get_ignore_packages()

    def gather_args(self, args: argparse.ArgumentParser) -> None:
        """Gather arguments.

        Args:
            args: Argument parser that arguments will be added to.
        """
        args.add_argument(
            "--output-directory",
            "-o",
            dest="output_directory",
            type=str,
            help="Directory to write output files to",
        )
        args.add_argument(
            "--log",
            dest="log_level",
            type=str,
            default="WARNING",
            help="Verbosity level of output to show (DEBUG, INFO, WARNING, ERROR"
            ", CRITICAL)",
        )
        args.add_argument(
            "--check",
            dest="check",
            action="store_true",
            help="Return the status. Return code 0 means there were no issues. \
                  Return code 1 means there were issues.",
        )
        args.add_argument(
            "--config", dest="config", type=str, help="Name of config yaml file"
        )
        args.add_argument(
            "--level",
            dest="level",
            type=str,
            help="Scan level to use from config file. \
                  Overrides any levels specified by the profile.",
        )
        args.add_argument(
            "--profile", dest="profile", type=str, help="Name of profile yaml file"
        )
        args.add_argument(
            "--exceptions",
            dest="exceptions",
            type=str,
            help="Name of exceptions yaml file",
        )
        args.add_argument(
            "--force-tool-list",
            dest="force_tool_list",
            type=str,
            help="Force only the given list of tools to run",
        )
        args.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {version('statick')}",
        )
        args.add_argument(
            "--tool-versions-all",
            action="store_true",
            dest="show_all_tool_versions",
            help="Show versions of all tools.",
        )
        args.add_argument(
            "--tool-versions-run",
            action="store_true",
            dest="show_run_tool_versions",
            help="Show versions of tools that are run at current level.",
        )
        args.add_argument(
            "--mapping-file-suffix",
            dest="mapping_file_suffix",
            type=str,
            help="Suffix to use when searching for CERT mapping files",
        )
        args.add_argument(
            "--timings",
            dest="timings",
            action="store_true",
            help="Enable printing timing information to stdout",
        )

        # Statick workspace arguments.
        args.add_argument(
            "-ws",
            dest="workspace",
            action="store_true",
            help="Treat the path argument as a workspace of multiple packages",
        )
        args.add_argument(
            "--max-procs",
            dest="max_procs",
            type=self.set_cpu_count,
            default=int(multiprocessing.cpu_count() / 2),
            help="Maximum number of CPU cores to use. "
            "Defaults to half the available CPU cores. Setting to -1 will "
            "cause Statick to use all available CPU cores",
        )
        args.add_argument(
            "--packages-file",
            dest="packages_file",
            type=str,
            help="File listing packages to scan, only used when running on a workspace",
        )
        args.add_argument(
            "--list-packages",
            dest="list_packages",
            action="store_true",
            help="List packages and levels, only used when running on a workspace",
        )

        for _, plugin in list(self.discovery_plugins.items()):
            plugin.gather_args(args)

        for _, plugin in list(self.reporting_plugins.items()):
            plugin.gather_args(args)

        for _, plugin in list(self.tool_plugins.items()):
            plugin.gather_args(args)

    def get_level(self, path: str, args: argparse.Namespace) -> Optional[str]:
        """Get level to scan package at.

        Args:
            path: Path to package.
            args: Arguments from command line.

        Returns:
            Level to scan package at.
        """
        path = os.path.abspath(path)

        if args.level is not None:
            return str(args.level)

        profile_filename = "profile.yaml"
        if args.profile is not None:
            profile_filename = args.profile
        profile_resource = self.resources.get_file(profile_filename)
        if profile_resource is None:
            logging.error("Could not find profile file %s!", profile_filename)
            return None
        try:
            profile = Profile(profile_resource)
        except OSError as ex:
            # This isn't quite redundant with the profile_resource check: it's possible
            # that something else triggers an OSError, like permissions.
            logging.error("Failed to access profile file %s: %s", profile_filename, ex)
            return None
        except ValueError as ex:
            logging.error("Profile file %s has errors: %s", profile_filename, ex)
            return None

        package = Package(os.path.basename(path), path)
        level = profile.get_package_level(package)

        return level

    def add_timing(
        self, package: str, name: str, plugin_type: str, duration: str
    ) -> None:
        """Add an entry to the timings list.

        Args:
            package: Name of the package.
            name: Name of the plugin.
            plugin_type: Type of the plugin.
            duration: Duration of the plugin execution.
        """
        timing = Timing(package, name, plugin_type, duration)
        self.timings.append(timing)

    def get_timings(self) -> list[Timing]:
        """Return list of timings for each component.

        Returns:
            List of timings for each component.
        """
        return self.timings

    def add_tool_version(self, tool: str, tool_version: str) -> None:
        """Add an entry to the tool versions list.

        Args:
            tool: Name of the tool.
            tool_version: Version of the tool.
        """
        this_tool_version = ToolVersion(tool, tool_version)
        self.tool_versions.append(this_tool_version)

    def get_tool_versions(self) -> list[ToolVersion]:
        """Return list of version for each tool.

        Returns:
            List of versions for each tool.
        """
        return self.tool_versions

    def collect_tool_versions(self, args: argparse.Namespace) -> bool:
        """Print out all tool versions.

        Args:
            args: Arguments from command line.

        Returns:
            True if successful, False otherwise.
        """
        success = True

        path = os.path.abspath(args.path)
        if not os.path.exists(path):
            logging.error("No package found at %s!", path)
            return False

        level: Optional[str] = self.get_level(path, args)
        logging.info("level: %s", level)
        if level is None:
            logging.error("Level is not valid.")
            return False

        if not self.config or (
            level != self.default_level and not self.config.has_level(level)
        ):
            logging.error("Can't find specified level %s in config!", level)
            return False

        plugin_context = PluginContext(args, self.resources, self.config)

        for plugin_name, plugin in list(self.tool_plugins.items()):
            plugin.set_plugin_context(plugin_context)
            self.add_tool_version(plugin_name, plugin.get_version())

        return success

    # pylint: disable=too-many-locals, too-many-return-statements, too-many-branches
    # pylint: disable=too-many-statements
    def run(
        self, path: str, args: argparse.Namespace, start_time: Optional[float] = None
    ) -> Tuple[Optional[dict[str, list[Issue]]], bool]:
        """Run scan tools against targets on path.

        Args:
            path: Path to the target.
            args: Arguments from command line.
            start_time: Start time of the scan.

        Returns:
            Issues found and success status.
        """
        success = True

        path = os.path.abspath(path)
        if not os.path.exists(path):
            logging.error("No package found at %s!", path)
            return None, False

        package = Package(os.path.basename(path), path)
        level: Optional[str] = self.get_level(path, args)
        logging.info("level: %s", level)
        if level is None:
            logging.error("Level is not valid.")
            return None, False

        if not self.config or (
            level != self.default_level and not self.config.has_level(level)
        ):
            logging.error("Can't find specified level %s in config!", level)
            return None, False

        orig_path = os.getcwd()
        if args.output_directory:
            if not os.path.isdir(args.output_directory):
                try:
                    os.mkdir(args.output_directory)
                except OSError as ex:
                    logging.error(
                        "Unable to create output directory at %s: %s",
                        args.output_directory,
                        ex,
                    )
                    return None, False

            output_dir = os.path.join(args.output_directory, package.name + "-" + level)

            if not os.path.isdir(output_dir):
                try:
                    os.mkdir(output_dir)
                except OSError as ex:
                    logging.error(
                        "Unable to create output directory at %s: %s", output_dir, ex
                    )
                    return None, False
            logging.info("Writing output to: %s", output_dir)

            os.chdir(output_dir)

        logging.info("------")
        logging.info(
            "Scanning package %s (%s) at level %s", package.name, package.path, level
        )

        issues: dict[str, list[Issue]] = {}

        ignore_packages = self.get_ignore_packages()
        if package.name in ignore_packages:
            logging.info(
                "Package %s is configured to be ignored by Statick.", package.name
            )
            return issues, True

        plugin_context = PluginContext(args, self.resources, self.config)

        logging.info("---Discovery---")
        if not DiscoveryPlugin.file_command_exists():
            logging.info(
                "file command isn't available, discovery plugins will be less effective"
            )

        discovery_plugins = self.config.get_enabled_discovery_plugins(level)
        if not discovery_plugins:
            discovery_plugins = list(self.discovery_plugins)
        # Get timing information for finding files for discovery plugins.
        dummy_plugin = DiscoveryPlugin()
        plugin_start = time.time()
        dummy_plugin.find_files(package)
        duration = format(time.time() - plugin_start, ".4f")
        timing = Timing(package.name, "find files", "Discovery", duration)
        self.timings.append(timing)

        plugins_ran: list[Any] = []
        for plugin_name in discovery_plugins:
            if plugin_name not in self.discovery_plugins:
                logging.error("Can't find specified discovery plugin %s!", plugin_name)
                return None, False

            plugin = self.discovery_plugins[plugin_name]
            dependencies = plugin.get_discovery_dependencies()
            for dependency_name in dependencies:
                dependency_plugin = self.discovery_plugins[dependency_name]
                if dependency_plugin.get_name() in plugins_ran:
                    continue
                dependency_plugin.set_plugin_context(plugin_context)
                logging.info(
                    "Running %s discovery plugin...", dependency_plugin.get_name()
                )
                plugin_start = time.time()
                dependency_plugin.scan(package, level, self.exceptions)
                duration = format(time.time() - plugin_start, ".4f")
                timing = Timing(
                    package.name, dependency_plugin.get_name(), "Discovery", duration
                )
                self.timings.append(timing)
                logging.info("%s discovery plugin done.", dependency_plugin.get_name())
                plugins_ran.append(dependency_plugin.get_name())

            if plugin.get_name() not in plugins_ran:
                plugin.set_plugin_context(plugin_context)
                logging.info("Running %s discovery plugin...", plugin.get_name())
                plugin_start = time.time()
                plugin.scan(package, level, self.exceptions)
                duration = format(time.time() - plugin_start, ".4f")
                timing = Timing(package.name, plugin.get_name(), "Discovery", duration)
                self.timings.append(timing)
                logging.info("%s discovery plugin done.", plugin.get_name())
                plugins_ran.append(plugin.get_name())
        logging.info("---Discovery---")

        logging.info("---Tools---")
        enabled_plugins = self.config.get_enabled_tool_plugins(level)
        if not enabled_plugins:
            enabled_plugins = list(self.tool_plugins)
        plugins_to_run = copy.copy(enabled_plugins)
        plugins_ran = []
        plugin_dependencies: list[str] = []
        while plugins_to_run:
            plugin_name = plugins_to_run[0]

            if plugin_name not in self.tool_plugins:
                logging.error("Can't find specified tool plugin %s!", plugin_name)
                return None, False

            if args.force_tool_list is not None:
                force_tool_list = args.force_tool_list.split(",")
                if (
                    plugin_name not in force_tool_list
                    and plugin_name not in plugin_dependencies
                ):
                    logging.info("Skipping plugin not in force list %s!", plugin_name)
                    plugins_to_run.remove(plugin_name)
                    continue

            plugin = self.tool_plugins[plugin_name]
            plugin.set_plugin_context(plugin_context)

            dependencies = plugin.get_tool_dependencies()
            dependencies_met = True
            for dependency_name in dependencies:
                if dependency_name not in plugins_ran:
                    if dependency_name not in enabled_plugins:
                        logging.error(
                            "Plugin %s depends on plugin %s which isn't enabled!",
                            plugin_name,
                            dependency_name,
                        )
                        return None, False
                    plugin_dependencies.append(dependency_name)
                    if dependency_name in plugins_to_run:
                        plugins_to_run.remove(dependency_name)
                    plugins_to_run.insert(0, dependency_name)
                    dependencies_met = False

            if not dependencies_met:
                continue

            logging.info("Running %s tool plugin...", plugin.get_name())
            plugin_start = time.time()
            tool_issues = plugin.scan(package, level)
            duration = format(time.time() - plugin_start, ".4f")
            timing = Timing(package.name, plugin.get_name(), "Tool", duration)
            self.timings.append(timing)
            self.add_tool_version(plugin.get_name(), plugin.get_version())
            if tool_issues is not None:
                issues[plugin_name] = tool_issues
                logging.info("%s tool plugin done.", plugin.get_name())
            else:
                logging.error("%s tool plugin failed", plugin.get_name())
                success = False

            plugins_to_run.remove(plugin_name)
            plugins_ran.append(plugin_name)

        logging.info("---Tools---")

        if self.exceptions is not None:
            issues = self.exceptions.filter_issues(package, issues)

        os.chdir(orig_path)

        logging.info("---Reporting---")
        reporting_plugins = self.config.get_enabled_reporting_plugins(level)
        if not reporting_plugins:
            if "print_to_console" in self.reporting_plugins:
                reporting_plugins = ["print_to_console"]
            else:
                reporting_plugins = list(self.reporting_plugins)
        for plugin_name in reporting_plugins:
            if plugin_name not in self.reporting_plugins:
                logging.error("Can't find specified reporting plugin %s!", plugin_name)
                return None, False

            plugin = self.reporting_plugins[plugin_name]
            plugin.set_plugin_context(plugin_context)
            logging.info("Running %s reporting plugin...", plugin.get_name())
            plugin_start = time.time()
            plugin.report(package, issues, level)
            duration = format(time.time() - plugin_start, ".4f")
            timing = Timing(package.name, plugin.get_name(), "Reporting", duration)
            self.timings.append(timing)
            logging.info("%s reporting plugin done.", plugin.get_name())
        logging.info("---Reporting---")

        if start_time is not None:
            duration = format(time.time() - start_time, ".4f")
            timing = Timing("Overall", "", "", duration)
            self.timings.append(timing)
        logging.info("Done!")

        return issues, success

    def run_workspace(
        self, parsed_args: argparse.Namespace, start_time: Optional[float] = None
    ) -> Tuple[
        Optional[dict[str, list[Issue]]], bool
    ]:  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Run statick on a workspace.

        Args:
            parsed_args: Parsed arguments from command line.
            start_time: Start time of the scan.

        Returns:
            Issues found and success status.
        """
        if parsed_args.output_directory:
            out_dir = parsed_args.output_directory
            if not os.path.isdir(out_dir):
                try:
                    os.mkdir(out_dir)
                except OSError as ex:
                    logging.error(
                        "Unable to create output directory at %s: %s", out_dir, ex
                    )
                    return None, False

        ignore_packages = self.get_ignore_packages()
        ignore_files = ["AMENT_IGNORE", "CATKIN_IGNORE", "COLCON_IGNORE"]
        package_indicators = ["package.xml", "setup.py", "pyproject.toml"]

        packages = []
        for root, dirs, files in os.walk(parsed_args.path):
            if any(item in files for item in ignore_files):
                dirs.clear()
                continue
            for sub_dir in dirs:
                full_dir = os.path.join(root, sub_dir)
                files = os.listdir(full_dir)
                if any(item in package_indicators for item in files) and not any(
                    item in files for item in ignore_files
                ):
                    if ignore_packages and sub_dir in ignore_packages:
                        continue
                    packages.append(Package(sub_dir, full_dir))

        if parsed_args.packages_file is not None:
            packages_file_list = []
            try:
                packages_file = os.path.abspath(parsed_args.packages_file)
                with open(packages_file, "r", encoding="utf8") as fname:
                    packages_file_list = [
                        package.strip()
                        for package in fname.readlines()
                        if package.strip() and package[0] != "#"
                    ]
            except OSError:
                logging.error("Packages file not found")
                return None, False
            packages = [
                package for package in packages if package.name in packages_file_list
            ]

        if parsed_args.list_packages:
            for package in packages:
                logging.info(
                    "%s: %s", package.name, self.get_level(package.path, parsed_args)
                )
            return None, True

        count = 0
        total_issues: list[Any] = []
        num_packages = len(packages)
        mp_args = []
        if multiprocessing.get_start_method() == "fork":
            logging.info("-- Scanning %d packages --", num_packages)
            for package in packages:
                count += 1
                mp_args.append((parsed_args, count, package, num_packages))

            with multiprocessing.Pool(parsed_args.max_procs) as pool:
                total_issues, all_timings = zip(  # type: ignore
                    *pool.starmap(self.scan_package, mp_args)
                )
                for timings in all_timings:
                    for timing in timings:
                        self.timings.append(timing)
        else:
            logging.warning(
                "Statick's plugin manager does not currently support multiprocessing"
                " without UNIX's fork function. Falling back to a single process."
            )
            logging.info("-- Scanning %d packages --", num_packages)
            for package in packages:
                count += 1
                pkg_issues, pkg_timings = self.scan_package(
                    parsed_args, count, package, num_packages
                )
                total_issues.append(pkg_issues)
                for timing in pkg_timings:
                    self.timings.append(timing)
                    break

        logging.info("-- All packages run --")
        logging.info("-- overall report --")

        success = True
        issues: dict[str, list[Issue]] = {}
        for issue in total_issues:
            if issue is not None:
                for key, value in list(issue.items()):
                    if key in issues:
                        issues[key] += value
                        if value:
                            success = False
                    else:
                        issues[key] = value
                        if value:
                            success = False

        enabled_reporting_plugins: list[str] = []

        # Make a fake 'all' package for reporting
        dummy_all_package = Package("all_packages", parsed_args.path)
        level = self.get_level(dummy_all_package.path, parsed_args)
        if level is not None and self.config is not None:
            if not self.config or not self.config.has_level(level):
                logging.error("Can't find specified level %s in config!", level)
            else:
                enabled_reporting_plugins = self.config.get_enabled_reporting_plugins(
                    level
                )

        if not enabled_reporting_plugins:
            if "print_to_console" in self.reporting_plugins:
                enabled_reporting_plugins = ["print_to_console"]
            else:
                enabled_reporting_plugins = list(self.reporting_plugins)

        plugin_context = PluginContext(parsed_args, self.resources, self.config)  # type: ignore
        plugin_context.args.output_directory = parsed_args.output_directory

        for plugin_name in enabled_reporting_plugins:
            if plugin_name not in self.reporting_plugins:
                logging.error("Can't find specified reporting plugin %s!", plugin_name)
                continue
            plugin = self.reporting_plugins[plugin_name]
            plugin.set_plugin_context(plugin_context)
            logging.info("Running %s reporting plugin...", plugin.get_name())
            plugin.report(dummy_all_package, issues, level)
            logging.info("%s reporting plugin done.", plugin.get_name())

        if start_time is not None:
            duration = format(time.time() - start_time, ".4f")
            timing = Timing("Overall", "", "", duration)
            self.timings.append(timing)

        return issues, success

    def scan_package(
        self,
        parsed_args: argparse.Namespace,
        count: int,
        package: Package,
        num_packages: int,
    ) -> Tuple[Optional[dict[str, list[Issue]]], list[Timing]]:
        """Scan each package in a separate process while buffering output.

        Args:
            parsed_args: Parsed arguments from command line.
            count: Current package count.
            package: Package to scan.
            num_packages: Total number of packages.

        Returns:
            Issues found and timings.
        """
        logger = logging.getLogger()
        old_handler = None
        handler = None
        if logger.handlers[0]:
            old_handler = logger.handlers[0]
            handler = MemoryHandler(10000, flushLevel=logging.ERROR, target=old_handler)
            logger.removeHandler(old_handler)
            logger.addHandler(handler)

        logging.info(
            "-- Scanning package %s (%d of %d) --", package.name, count, num_packages
        )

        sio = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = sio
        sys.stderr = sio

        issues, dummy = self.run(package.path, parsed_args)
        timings = self.get_timings()

        sys.stdout = old_stdout
        sys.stderr = old_stderr
        logging.info(sio.getvalue())

        if issues is not None:
            logging.info(
                "-- Done scanning package %s (%d of %d) --",
                package.name,
                count,
                num_packages,
            )
        else:
            logging.error("Failed to run statick on package %s!", package.name)

        if handler is not None and old_handler is not None:
            handler.flush()
            logger.removeHandler(handler)
            logger.addHandler(old_handler)

        return issues, timings

    @staticmethod
    def print_no_issues() -> None:
        """Print that no information about issues was found."""
        logging.error(
            "Something went wrong, no information about issues."
            " Statick exiting with errors."
        )

    @staticmethod
    def print_exit_status(status: bool) -> None:
        """Print Statick exit status.

        Args:
            status: Exit status.
        """
        if status:
            logging.info("Statick exiting with success.")
        else:
            logging.error("Statick exiting with errors.")
