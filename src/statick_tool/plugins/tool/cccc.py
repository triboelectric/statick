r"""Apply CCCC tool and gather results.

To run the CCCC tool locally (without Statick) one way to do so is:

find . -name \*.h -print -o -name \*.cpp -print | xargs cccc

That will generate several reports, including HTML. The results can be viewd in a web
browser.
"""

import argparse
import csv
import logging
import subprocess
from pathlib import Path
from typing import Any

import xmltodict
import yaml

from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.tool_plugin import ToolPlugin


class CCCCToolPlugin(ToolPlugin):
    """Apply CCCC tool and gather results."""

    def get_name(self) -> str:
        """Get name of tool.

        Returns:
            Name of the tool.
        """
        return "cccc"

    def gather_args(self, args: argparse.Namespace) -> None:
        """Gather arguments.

        Args:
            args: Flags for this plugin will be added to these existing arguments.
        """
        args.add_argument(
            "--cccc-bin", dest="cccc_bin", type=str, help="cccc binary path"
        )
        args.add_argument(
            "--cccc-config", dest="cccc_config", type=str, help="cccc config file"
        )

    def get_binary(  # pylint: disable=unused-argument
        self, level: str | None = None, package: Package | None = None
    ) -> str:
        """Get tool binary name.

        Args:
            level: The level of the scan.
            package: The package to scan.

        Returns:
            The name of the tool binary.
        """
        binary = self.get_name()
        if (
            self.plugin_context is not None
            and self.plugin_context.args.cccc_bin is not None
        ):
            binary = self.plugin_context.args.cccc_bin
        return binary

    def get_version(self) -> str:
        """Figure out and return the version of the tool that's installed.

        If no version is found the function returns "Uninstalled".

        Returns:
            The version of the tool.
        """
        return self.get_version_from_apt()

    def scan(  # pylint: disable=too-many-branches,too-many-locals
        self, package: Package, level: str
    ) -> list[Issue] | None:
        """Run tool and gather output.

        Args:
            package: The package to scan.
            level: The level of the scan.

        Returns:
            A list of issues found by the tool.
        """
        if "c_src" not in package.keys() or not package["c_src"]:
            return []

        if self.plugin_context is None:
            return None

        cccc_bin = self.get_binary()

        cccc_config = "cccc.opt"
        if self.plugin_context.args.cccc_config is not None:
            cccc_config = self.plugin_context.args.cccc_config
        config_file = self.plugin_context.resources.get_file(cccc_config)
        if config_file is not None:
            opts = ["--opt_infile=" + config_file]
        else:
            return []
        opts.append(" --lang=c++")

        issues: list[Issue] = []

        for src in package["c_src"]:
            tool_output_dir: str = ".cccc-" + Path(src).name
            opts.append("--outdir=" + tool_output_dir)

            try:
                subproc_args: list[str] = [cccc_bin] + opts + [src]
                logging.debug(" ".join(subproc_args))
                log_output: bytes = subprocess.check_output(
                    subproc_args, stderr=subprocess.STDOUT
                )
            except subprocess.CalledProcessError as ex:
                if ex.returncode == 1:
                    log_output = ex.output
                else:
                    logging.warning("Problem %d", ex.returncode)
                    logging.warning("%s exception: %s", self.get_name(), ex.output)
                    return None

            except OSError as ex:
                logging.warning("Couldn't find cccc executable! (%s)", ex)
                return None

            logging.debug("%s", log_output)

            if self.plugin_context and self.plugin_context.args.output_directory:
                with open(self.get_name() + ".log", "ab") as flog:
                    flog.write(log_output)

            try:
                with open(tool_output_dir + "/cccc.xml", encoding="utf8") as fresults:
                    tool_output = xmltodict.parse(
                        fresults.read(), dict_constructor=dict
                    )
            except FileNotFoundError:
                continue

            issues.extend(self.parse_tool_output(tool_output, src, config_file))
        return issues

    def parse_tool_output(  # pylint: disable=too-many-branches
        self, output: dict[Any, Any], src: str, config_file: str
    ) -> list[Issue]:
        """Parse tool output and report issues.

        Args:
            output: The output from the tool.
            src: The source file being scanned.
            config_file: The configuration file.

        Returns:
            A list of issues found by the tool.
        """
        if "CCCC_Project" not in output:
            return []

        config = self.parse_config(config_file)
        logging.debug(config)

        results: dict[Any, Any] = {}
        logging.debug(yaml.dump(output))
        if (
            "structural_summary" in output["CCCC_Project"]
            and output["CCCC_Project"]["structural_summary"]
            and "module" in output["CCCC_Project"]["structural_summary"]
        ):
            for module in output["CCCC_Project"]["structural_summary"]["module"]:
                if "name" not in module or isinstance(module, str):
                    break
                metrics: dict[Any, Any] = {}
                for field in module:
                    metrics[field] = {}
                    if "@value" in module[field]:
                        metrics[field]["value"] = module[field]["@value"]
                    if "@level" in module[field]:
                        metrics[field]["level"] = module[field]["@level"]
                results[module["name"]] = metrics

        if (
            "procedural_summary" in output["CCCC_Project"]
            and output["CCCC_Project"]["procedural_summary"]
            and "module" in output["CCCC_Project"]["procedural_summary"]
        ):
            for module in output["CCCC_Project"]["procedural_summary"]["module"]:
                if "name" not in module or isinstance(module, str):
                    break
                metrics = results[module["name"]]
                for field in module:
                    metrics[field] = {}
                    if "@value" in module[field]:
                        metrics[field]["value"] = module[field]["@value"]
                    if "@level" in module[field]:
                        metrics[field]["level"] = module[field]["@level"]
                results[module["name"]] = metrics

        if (
            "oo_design" in output["CCCC_Project"]
            and output["CCCC_Project"]["oo_design"]
            and "module" in output["CCCC_Project"]["oo_design"]
        ):
            for module in output["CCCC_Project"]["oo_design"]["module"]:
                if "name" not in module or isinstance(module, str):
                    break
                metrics = results[module["name"]]
                for field in module:
                    metrics[field] = {}
                    if "@value" in module[field]:
                        metrics[field]["value"] = module[field]["@value"]
                    if "@level" in module[field]:
                        metrics[field]["level"] = module[field]["@level"]
                results[module["name"]] = metrics

        issues: list[Issue] = self.find_issues(config, results, src)

        return issues

    @classmethod
    def parse_config(cls, config_file: str) -> dict[str, str]:
        """Parse CCCC configuration file.

        Gets warning and error thresholds for all the metrics. An explanation to dump
        default values to a configuration file is at:
        http://sarnold.github.io/cccc/CCCC_User_Guide.html#config

        `cccc --opt_outfile=cccc.opt`

        Args:
            config_file: The configuration file.

        Returns:
            A dictionary containing the parsed configuration.
        """
        config: dict[Any, Any] = {}

        if config_file is None:
            return config

        with open(config_file, "r", encoding="utf8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter="@")
            for row in reader:
                if row["CCCC_FileExt"] == "CCCC_MetTmnt":
                    config[row[".ADA"]] = {
                        "warn": row["ada.95"],
                        "error": row[""],
                        "name": row[None][3],
                        "key": row[".ADA"],
                    }

        return config

    def find_issues(
        self, config: dict[Any, Any], results: dict[Any, Any], src: str
    ) -> list[Issue]:
        """Identify issues by comparing tool results with tool configuration.

        Args:
            config: The configuration dictionary.
            results: The results dictionary.
            src: The source file being scanned.

        Returns:
            A list of issues found by the tool.
        """
        issues: list[Issue] = []
        dummy = []

        logging.debug("Results")
        logging.debug(results)
        for key, val in results.items():
            for item in val.keys():
                val_id = self.convert_name_to_id(item)
                if val_id != "" and val_id in config.keys():
                    if val[item]["value"] == "------" or val[item]["value"] == "******":
                        dummy.append("only here for code coverage")
                        continue
                    result = float(val[item]["value"])
                    thresh_error = float(config[val_id]["error"])
                    thresh_warn = float(config[val_id]["warn"])
                    msg = key + " - " + config[val_id]["name"]
                    msg += f" - value: {result}, thresholds warning: {thresh_warn}"
                    msg += f", error: {thresh_error}"
                    if ("level" in val[item] and val[item]["level"] == "2") or (
                        result > thresh_error
                    ):
                        issues.append(
                            Issue(
                                src,
                                0,
                                self.get_name(),
                                "error",
                                5,
                                msg,
                                None,
                            )
                        )
                    elif ("level" in val[item] and val[item]["level"] == "1") or (
                        result > thresh_warn
                    ):
                        issues.append(
                            Issue(
                                src,
                                0,
                                self.get_name(),
                                "warn",
                                3,
                                msg,
                                None,
                            )
                        )

        return issues

    @classmethod
    def convert_name_to_id(cls, name: str) -> str:  # pylint: disable=too-many-branches
        """Convert result name to configuration name.

        The name given in CCCC results is different than the name given in CCCC
        configuration. This will map the name in the configuration file to the name
        given in the results.

        Args:
            name: The name to convert.

        Returns:
            The converted name.
        """
        name_id = ""

        if name == "IF4":
            name_id = "IF4"
        elif name == "fan_out_concrete":
            name_id = "FOc"
        elif name == "IF4_visible":
            name_id = "IF4v"
        elif name == "coupling_between_objects":
            name_id = "CBO"
        elif name == "fan_in_visible":
            name_id = "FIv"
        elif name == "weighted_methods_per_class_unity":
            name_id = "WMC1"
        elif name == "fan_out":
            name_id = "FO"
        elif name == "weighted_methods_per_class_visibility":
            name_id = "WMCv"
        elif name == "fan_out_visible":
            name_id = "FOv"
        elif name == "IF4_concrete":
            name_id = "IF4c"
        elif name == "depth_of_inheritance_tree":
            name_id = "DIT"
        elif name == "number_of_children":
            name_id = "NOC"
        elif name == "fan_in_concrete":
            name_id = "FIc"
        elif name == "fan_in":
            name_id = "FI"
        elif name == "lines_of_comment":
            name_id = "COM"
        elif name == "lines_of_code_per_line_of_comment":
            name_id = "L_C"
        elif name == "McCabes_cyclomatic_complexity":
            name_id = "MVGper"
        elif name == "lines_of_code":
            name_id = "LOCp"
        elif name == "McCabes_cyclomatic_complexity_per_line_of_comment":
            name_id = "M_C"

        return name_id
