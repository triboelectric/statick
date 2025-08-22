"""Unit tests for the ruff plugin."""

import argparse
import os
import json
import subprocess
import sys

import mock

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.ruff import RuffToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_ruff_tool_plugin():
    """Initialize and return a ruff plugin."""
    arg_parser = argparse.ArgumentParser()

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    rtp = RuffToolPlugin()
    rtp.set_plugin_context(plugin_context)
    return rtp


def test_ruff_tool_plugin_found():
    """Test that the plugin manager can find the ruff plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(plugin.get_name() == "ruff" for _, plugin in list(plugins.items()))


def test_ruff_tool_plugin_scan_valid():
    """Integration test: Make sure the ruff output hasn't changed."""
    rtp = setup_ruff_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "ruff_test.py")
    ]
    issues = rtp.scan(package, "level")
    assert len(issues) == 1


def test_ruff_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of ruff."""
    rtp = setup_ruff_tool_plugin()
    output = {
        "code": "E501",
        "filename": "some_file.py",
        "location": {"column": 89, "row": 644},
        "message": "Line too long (96 > 88 characters)",
    }
    issues = rtp.parse_output([json.dumps(output)])
    assert len(issues) == 1
    assert issues[0].filename == "some_file.py"
    assert issues[0].line_number == 644
    assert issues[0].tool == "ruff"
    assert issues[0].issue_type == "E501"
    assert issues[0].severity == 5
    assert issues[0].message == "Line too long (96 > 88 characters)"

    output = {
        "code": "E402",
        "filename": "a_file.py",
        "location": {"column": 1, "row": 21},
        "message": "Module level import not at top of file",
    }
    issues = rtp.parse_output([json.dumps(output)])
    assert len(issues) == 1
    assert issues[0].filename == "a_file.py"
    assert issues[0].line_number == 21
    assert issues[0].tool == "ruff"
    assert issues[0].issue_type == "E402"
    assert issues[0].severity == 5
    assert issues[0].message == "Module level import not at top of file"


def test_ruff_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of ruff."""
    rtp = setup_ruff_tool_plugin()
    output = "invalid text"
    issues = rtp.parse_output([output])
    assert not issues


@mock.patch("statick_tool.plugins.tool.ruff.subprocess.check_output")
def test_ruff_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means ruff hit an
    error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    rtp = setup_ruff_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "ruff_test.py")
    ]
    issues = rtp.scan(package, "level")
    assert not issues

    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        32, "", output="mocked error"
    )
    issues = rtp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.ruff.subprocess.check_output")
def test_ruff_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means ruff doesn't exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    rtp = setup_ruff_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "ruff_test.py")
    ]
    issues = rtp.scan(package, "level")
    assert issues is None
