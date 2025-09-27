"""Unit tests for the cppcheck plugin."""

import argparse
import os
import subprocess
import sys

import mock
import pytest
from packaging.version import Version

import statick_tool
from statick_tool.config import Config
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.plugins.tool.cppcheck import CppcheckToolPlugin
from statick_tool.resources import Resources

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


def setup_cppcheck_tool_plugin(use_plugin_context=True, binary=None):
    """Initialize and return an instance of the cppcheck plugin."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--cppcheck-bin", dest="cppcheck_bin")
    arg_parser.add_argument(
        "--mapping-file-suffix", dest="mapping_file_suffix", type=str
    )

    resources = Resources(
        [os.path.join(os.path.dirname(statick_tool.__file__), "plugins")]
    )
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    plugin_context.args.output_directory = os.path.dirname(__file__)
    cctp = CppcheckToolPlugin()
    if binary:
        plugin_context.args.cppcheck_bin = binary
    if use_plugin_context:
        cctp.set_plugin_context(plugin_context)
    return cctp


def test_cppcheck_tool_plugin_found():
    """Test that the plugin manager can find the cppcheck plugin."""
    plugins = {}
    tool_plugins = entry_points(group="statick_tool.plugins.tool")
    for plugin_type in tool_plugins:
        plugin = plugin_type.load()
        plugins[plugin_type.name] = plugin()
    assert any(plugin.get_name() == "cppcheck" for _, plugin in list(plugins.items()))


def test_cppcheck_tool_plugin_scan_valid():
    """Integration test: Make sure the cppcheck output hasn't changed."""
    if sys.platform == "win32":
        pytest.skip(
            "Running cppcheck on GitHub Windows runner is failing. Skipping test."
        )
    cctp = setup_cppcheck_tool_plugin(use_plugin_context=True)
    if not cctp.command_exists("cppcheck"):
        pytest.skip("Can't find cppcheck, unable to test cppcheck plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )

    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
    ]
    package["make_targets"][0]["include_dirs"] = [
        os.path.join(os.path.dirname(__file__), "valid_package")
    ]
    package["headers"] = []
    package["path"] = os.path.join(os.path.dirname(__file__), "valid_package")
    issues = cctp.scan(package, "level")
    assert len(issues) == 1
    assert issues[0].filename == os.path.join(
        os.path.dirname(__file__), "valid_package", "test.c"
    )
    assert issues[0].line_number == 4
    assert issues[0].tool == "cppcheck"
    version = cctp.parse_version(cctp.get_version())
    if Version(version) >= Version("2.8"):
        assert issues[0].issue_type == "error/legacyUninitvar"
    else:
        assert issues[0].issue_type == "error/uninitvar"
    assert issues[0].severity == 5
    assert issues[0].message == "Uninitialized variable: si"


def test_cppcheck_tool_plugin_scan_no_plugin_context():
    """Test that issues are None when no plugin context is provided."""
    cctp = setup_cppcheck_tool_plugin(use_plugin_context=False)
    if not cctp.command_exists("cppcheck"):
        pytest.skip("Can't find cppcheck, unable to test cppcheck plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = []
    package["headers"] = []
    issues = cctp.scan(package, "level")
    assert not issues


def test_cppcheck_tool_plugin_scan_wrong_binary():
    """Test that issues are None when wrong binary is provided."""
    cctp = setup_cppcheck_tool_plugin(binary="wrong_binary")
    if not cctp.command_exists("cppcheck"):
        pytest.skip("Can't find cppcheck, unable to test cppcheck plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = []
    package["headers"] = []
    issues = cctp.scan(package, "level")
    assert not issues


def test_cppcheck_tool_plugin_scan_no_files():
    """Check what happens if the plugin isn't passed any files."""
    cctp = setup_cppcheck_tool_plugin()
    if not cctp.command_exists("cppcheck"):
        pytest.skip("Can't find cppcheck, unable to test cppcheck plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = []
    package["headers"] = []
    issues = cctp.scan(package, "level")
    assert not issues


def test_cppcheck_tool_plugin_scan_invalid_file():
    """Check what happens if the plugin is passed an invalid file."""
    cctp = setup_cppcheck_tool_plugin()
    if not cctp.command_exists("cppcheck"):
        pytest.skip("Can't find cppcheck, unable to test cppcheck plugin")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )

    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "nope.c")
    ]
    package["headers"] = []
    # This should raise a calledProcessError, so None will be returned
    issues = cctp.scan(package, "level")
    assert issues is None


def test_cppcheck_tool_plugin_parse_valid():
    """Verify that we can parse the normal output of cppcheck."""
    cctp = setup_cppcheck_tool_plugin()
    output = "[test.c:4]: (error uninitvar) Uninitialized variable: si"
    issues = cctp.parse_tool_output(output)
    assert len(issues) == 1
    assert issues[0].filename == "test.c"
    assert issues[0].line_number == 4
    assert issues[0].tool == "cppcheck"
    assert issues[0].issue_type == "error/uninitvar"
    assert issues[0].severity == 5
    assert issues[0].message == "Uninitialized variable: si"


def test_cppcheck_tool_plugin_parse_invalid():
    """Verify that we can parse the normal output of cppcheck."""
    cctp = setup_cppcheck_tool_plugin()
    output = "invalid text"
    issues = cctp.parse_tool_output(output)
    assert not issues


def test_cppcheck_tool_plugin_scan_missing_fields():
    """Test what happens when key fields are missing from the Package argument.

    Expected result: issues is empty
    """
    cctp = setup_cppcheck_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    # Missing make_targets
    issues = cctp.scan(package, "level")
    assert not issues


@mock.patch("statick_tool.plugins.tool.cppcheck.subprocess.check_output")
def test_cppcheck_tool_plugin_scan_oserror(mock_subprocess_check_output):
    """Test what happens when an OSError is raised (usually means cppcheck doesn't
    exist).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = OSError("mocked error")
    cctp = setup_cppcheck_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
    ]
    package["headers"] = []
    issues = cctp.scan(package, "level")
    assert issues is None


def calledprocesserror_helper(*popenargs, **kwargs):
    """Helper for the calledprocesserror test.

    Lambdas can't raise exceptions, so this logic gets its own function.
    """
    # Workaround so that the --version check doesn't throw a CalledProcessError
    if "--version" in popenargs[0]:
        return b"1.2.3"
    else:
        raise subprocess.CalledProcessError(2, "", output="mocked error")


@mock.patch("statick_tool.plugins.tool.cppcheck.subprocess.check_output")
def test_cppcheck_tool_plugin_scan_calledprocesserror(mock_subprocess_check_output):
    """Test what happens when a CalledProcessError is raised (usually means cppcheck hit
    an error).

    Expected result: issues is None
    """
    mock_subprocess_check_output.side_effect = calledprocesserror_helper
    cctp = setup_cppcheck_tool_plugin()
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
    ]
    package["headers"] = []
    issues = cctp.scan(package, "level")
    assert issues is None


def test_checkforexceptions_true():
    """Test check_for_exceptions behavior where it should return True."""
    mm = mock.MagicMock()
    mm.group.side_effect = lambda i: (
        "test.c" if i == 1 else "variableScope" if i == 4 else False
    )
    assert CppcheckToolPlugin.check_for_exceptions(mm)


def test_checkforexceptions_false():
    """Test check_for_exceptions behavior where it should return False."""
    mm = mock.MagicMock()
    mm.group.side_effect = lambda i: (
        "test.c" if i == 1 else "some-other-error" if i == 6 else False
    )
    assert not CppcheckToolPlugin.check_for_exceptions(mm)


@mock.patch("statick_tool.plugins.tool.cppcheck.subprocess.check_output")
def test_cppcheck_tool_plugin_version_match(mock_subprocess_check_output):
    """Test the result of passing a requested version to the plugin when that version
    isn't available."""
    mock_subprocess_check_output.return_value = b"Cppcheck 1.2"
    cctp = setup_cppcheck_tool_plugin()
    # Mock the return value of self.plugin_context.config.get_tool_config
    cctp.plugin_context.config.get_tool_config = mock.MagicMock(return_value="1.3")
    package = Package(
        "valid_package", os.path.join(os.path.dirname(__file__), "valid_package")
    )
    package["make_targets"] = []
    package["make_targets"].append({})
    package["make_targets"][0]["src"] = [
        os.path.join(os.path.dirname(__file__), "valid_package", "test.c")
    ]
    package["headers"] = []
    issues = cctp.scan(package, "level")
    assert issues is None
