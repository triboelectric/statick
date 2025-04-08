"""Unit tests for the pyright plugin."""

import argparse
import json
import os
import subprocess
import sys

import mock
import pytest
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.resources import Resources

import statick_tool
from statick_tool.plugins.tool.pyright import PyrightToolPlugin

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_pyright_tool_plugin(test_package="valid_package"):
    """Initialize and return an instance of the pyright plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--show-tool-output",
        dest="show_tool_output",
        action="store_false",
        help="Show tool output",
    )

    resources = Resources(
        [
            os.path.join(os.path.dirname(statick_tool.__file__), "plugins"),
            os.path.join(os.path.dirname(__file__), test_package),
        ]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    plugin = PyrightToolPlugin()
    plugin.set_plugin_context(plugin_context)
    return plugin


def test_pyright_tool_plugin_found():
    """Test that the plugin manager can find the pyright plugin."""
    tool_plugins = {}
    plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in plugins:
        plugin = plugin_type.load()
        tool_plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "pyright" for _, plugin in list(tool_plugins.items())
    )


def test_pyright_tool_plugin_scan_valid():
    """Integration test: Make sure the pyright output hasn't changed."""
    plugin = setup_pyright_tool_plugin(test_package="valid_package")
    if not plugin.command_exists("pyright"):
        pytest.skip("Missing pyright executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "good.py")
    ]
    issues = plugin.scan(package, "level")
    assert not issues


def test_pyright_tool_plugin_scan_valid_with_issues():
    """Integration test: Make sure the pyright output hasn't changed."""
    plugin = setup_pyright_tool_plugin(test_package="valid_package")
    if not plugin.command_exists("pyright"):
        pytest.skip("Missing pyright executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "bad.py")
    ]
    issues = plugin.scan(package, "level")
    assert len(issues) == 1


def test_pyright_tool_plugin_parse_valid():
    """Verify that we can parse the expected output of pyright."""
    plugin = setup_pyright_tool_plugin()
    output = "{\"version\": \"0.0.0\", \"generalDiagnostics\": [{\"file\": \"test.py\", \"severity\": \"error\", \"message\": \"Error message\", \"range\": {\"start\": {\"line\": 1, \"character\": 1}, \"end\": {\"line\": 1, \"character\": 2}}, \"rule\": \"reportReturnType\"}], \"summary\": {\"filesAnalyzed\": 1, \"errorCount\": 1, \"warningCount\": 0, \"informationCount\": 0, \"timeInSec\": 0.174}}"
    issues = plugin.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "test.py"
    assert issues[0].line_number == 1
    assert issues[0].tool == "pyright"
    assert issues[0].issue_type == "reportReturnType"
    assert issues[0].severity == 5
    assert issues[0].message == "Error message"

    output = "{\"version\": \"0.0.0\", \"generalDiagnostics\": [{\"file\": \"test.py\", \"severity\": \"warning\", \"message\": \"Error message\", \"range\": {\"start\": {\"line\": 1, \"character\": 1}, \"end\": {\"line\": 1, \"character\": 2}}, \"rule\": \"reportReturnType\"}], \"summary\": {\"filesAnalyzed\": 1, \"errorCount\": 1, \"warningCount\": 0, \"informationCount\": 0, \"timeInSec\": 0.174}}"
    issues = plugin.parse_output([output])
    assert issues[0].severity == 3

    output = "{\"version\": \"0.0.0\", \"generalDiagnostics\": [{\"file\": \"test.py\", \"severity\": \"gobbledeegook\", \"message\": \"Error message\", \"range\": {\"start\": {\"line\": 1, \"character\": 1}, \"end\": {\"line\": 1, \"character\": 2}}, \"rule\": \"reportReturnType\"}], \"summary\": {\"filesAnalyzed\": 1, \"errorCount\": 1, \"warningCount\": 0, \"informationCount\": 0, \"timeInSec\": 0.174}}"
    issues = plugin.parse_output([output])
    assert issues[0].severity == 1


def test_pyright_tool_plugin_parse_invalid():
    """Verify that invalid output of pyright is ignored."""
    plugin = setup_pyright_tool_plugin()
    # Leave out the "generalDiagnostics" key to simulate invalid output.
    output = "{\"nonsense\": \"0.0.0\"}"
    issues = plugin.parse_output([output])
    assert not issues


@mock.patch("statick_tool.plugins.tool.pyright.subprocess.check_output")
def test_pyright_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """
    Test what happens when a CalledProcessError is raised (usually means pyright hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    plugin = setup_pyright_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "good.py")
    ]
    issues = plugin.scan(package, "level")
    assert not issues

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    issues = plugin.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.pyright.subprocess.check_output")
def test_pyright_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """
    Test what happens when an OSError is raised (usually means pyright doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    plugin = setup_pyright_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "good.py")
    ]
    issues = plugin.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.pyright.subprocess.check_output")
def test_pyright_tool_plugin_scan_ioerror(mock_subprocess_check_output):
    """
    Test what happens when an IOError is raised (usually means pyright doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = IOError("mocked error")
    plugin = setup_pyright_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "good.py")
    ]
    issues = plugin.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.pyright.json.loads")
def test_pyright_tool_plugin_parse_output_value_error(mock_json_loads):
    """
    Test what happens when a ValueError is raised while reading JSON data.

    Expected result: issues is None
    """
    mock_json_loads.side_effect = ValueError("mocked error")
    plugin = setup_pyright_tool_plugin()
    output = "some made up text to parse"
    issues = plugin.parse_output([output])
    assert not issues
