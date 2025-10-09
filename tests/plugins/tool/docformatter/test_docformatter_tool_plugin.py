"""Unit tests for the docformatter plugin."""

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
from statick_tool.plugins.tool.docformatter import DocformatterToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_docformatter_tool_plugin():
    """Create and return an instance of the Docformatter plugin."""
    arg_parser = argparse.ArgumentParser()

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    dtp = DocformatterToolPlugin()
    dtp.set_plugin_context(plugin_context)
    return dtp


def test_docformatter_tool_plugin_found():
    """Test that the plugin manager can find the Docformatter plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(
        plugin.get_name() == "docformatter" for _, plugin in list(plugins.items())
    )


def test_docformatter_tool_plugin_scan_valid():
    """Integration test: Make sure the docformatter output hasn't changed."""
    dtp = setup_docformatter_tool_plugin()
    if not dtp.command_exists("docformatter"):
        pytest.skip("Can't find docformatter, unable to test docformatter plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "wrong.py")
    ]
    issues = dtp.scan(package, "level")
    assert len(issues) == 1


def test_docformatter_tool_plugin_scan_invalid():
    """Make sure no issues are found when no Python source files are available."""
    dtp = setup_docformatter_tool_plugin()
    if not dtp.command_exists("docformatter"):
        pytest.skip("Can't find docformatter, unable to test docformatter plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    issues = dtp.scan(package, "level")
    assert not issues


def test_docformatter_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of docformatter."""
    dtp = setup_docformatter_tool_plugin()
    output = os.path.join("valid_package", "wrong.py")
    issues = dtp.parse_output([output])
    assert len(issues) == 1
    assert issues[0].filename == os.path.join("valid_package", "wrong.py")
    assert issues[0].line_number == 0
    assert issues[0].tool == "docformatter"
    assert issues[0].issue_type == "format"
    assert issues[0].severity == 3
    assert issues[0].message == "would reformat"


def test_docformatter_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of docformatter."""
    dtp = setup_docformatter_tool_plugin()
    output = "invalid text"
    issues = dtp.parse_output(output)
    assert not issues


def test_docformatter_version_not_supported(mocker):
    """Test that docformatter handles Python 3.14+ correctly."""
    if sys.version_info < (3, 14):
        pytest.skip("This test is only for Python 3.14+")
    mocker.patch("sys.version_info", (3, 14))
    dtp = setup_docformatter_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "wrong.py")
    ]
    issues = dtp.scan(package, "level")
    assert not issues

@mock.patch(
    "statick_tool.plugins.tool.docformatter.subprocess.check_output"
)
def test_docformatter_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means docformatter doesn't
    exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    dtp = setup_docformatter_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "wrong.py")
    ]
    issues = dtp.scan(package, "level")
    assert not issues


@mock.patch(
    "statick_tool.plugins.tool.docformatter.subprocess.check_output"
)
def test_docformatter_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means docformatter
    hit an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = subprocess.CalledProcessError(
        0, "", output="mocked error"
    )
    dtp = setup_docformatter_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["python_src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "e501.py")
    ]
    issues = dtp.scan(package, "level")
    assert not issues
