"""xmllint unit tests."""

import argparse
import os
import subprocess
import sys

import mock
import pytest

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.xmllint import XmllintToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_xmllint_tool_plugin():
    """Create an instance of the xmllint plugin."""
    arg_parser = argparse.ArgumentParser()

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    xltp = XmllintToolPlugin()
    xltp.set_plugin_context(plugin_context)
    return xltp


def test_xmllint_tool_plugin_found():
    """Test that the plugin manager finds the xmllint plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "xmllint" for _, plugin in list(plugins.items())
    )


def test_xmllint_tool_plugin_scan_valid():
    """Integration test: Make sure the xmllint output hasn't changed."""
    if sys.platform == "win32":
        pytest.skip(
            "Running xmllint on GitHub Windows runner is failing. Skipping test."
        )
    xltp = setup_xmllint_tool_plugin()
    if not xltp.command_exists("xmllint"):
        pytest.skip("Missing xmllint executable.")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["xml"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "premature_end.xml")
    ]
    issues = xltp.scan(package, "level")
    assert len(issues) == 2


def test_xmllint_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of xmllint."""
    xltp = setup_xmllint_tool_plugin()
    output = "valid_package/premature_end.xml:3: parser error : Opening and ending tag mismatch: notclosed line 2 and tag"
    issues = xltp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == "valid_package/premature_end.xml"
    assert issues[0].line_number == 3
    assert issues[0].tool == "xmllint"
    assert issues[0].issue_type == "parser error"
    assert issues[0].severity == 5
    assert (
        issues[0].message == "Opening and ending tag mismatch: notclosed line 2 and tag"
    )


def test_xmllint_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of xmllint."""
    xltp = setup_xmllint_tool_plugin()
    output = "invalid text"
    issues = xltp.parse_output(output)
    assert not issues


@mock.patch("statick_tool.plugins.tool.xmllint.subprocess.check_output")
def test_xmllint_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means xmllint hit
    an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        2, "", output="mocked error"
    )
    xltp = setup_xmllint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["xml"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "premature_end.xml")
    ]
    issues = xltp.scan(package, "level")
    assert issues is None


@mock.patch("statick_tool.plugins.tool.xmllint.subprocess.check_output")
def test_xmllint_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means xmllint doesn't
    exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    xltp = setup_xmllint_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["xml"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "premature_end.xml")
    ]
    issues = xltp.scan(package, "level")
    assert issues is None
