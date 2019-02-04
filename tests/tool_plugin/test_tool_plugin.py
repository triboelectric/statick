"""Tests for statick_tool.tool_plugin."""
import argparse
import os
import shutil
import stat
import sys
import tempfile

import pytest

from statick_tool.config import Config
from statick_tool.plugin_context import PluginContext
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin


def test_tool_plugin_load_mapping_valid():
    """Test that we can load the warnings mapping."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'good_config')])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert len(mapping) == 1
    assert mapping == {'a': 'TST1-NO'}


def test_tool_plugin_load_mapping_invalid():
    """Test that we correctly skip invalid entries."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'bad_config')])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert not mapping


def test_tool_plugin_load_mapping_missing():
    """Test that we return an empty dict for missing files."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'missing_config')])
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, None)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    mapping = tp.load_mapping()
    assert not mapping


def test_tool_plugin_get_user_flags_invalid_level():
    """Test that we return an empty list for invalid levels."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'user_flags_config')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    flags = tp.get_user_flags('level2', name='test')
    assert flags == []


def test_tool_plugin_get_user_flags_invalid_tool():
    """Test that we return an empty list for undefined tools."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'user_flags_config')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    flags = tp.get_user_flags('level', name='test2')
    assert flags == []


def test_tool_plugin_get_user_flags_no_config():
    """Test that we return an empty list for missing configs."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'user_flags_config_missing')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    flags = tp.get_user_flags('level', name='test')
    assert flags == []


def test_tool_plugin_get_user_flags_valid_flags():
    """Test that we return a list of user flags."""
    arg_parser = argparse.ArgumentParser()
    resources = Resources([os.path.join(os.path.dirname(__file__), 'user_flags_config')])
    config = Config(resources.get_file("config.yaml"))
    plugin_context = PluginContext(arg_parser.parse_args([]), resources, config)
    tp = ToolPlugin()
    tp.set_plugin_context(plugin_context)
    flags = tp.get_user_flags('level', name='test')
    assert flags == ['look', 'a', 'flag']


def test_tool_plugin_is_valid_executable_valid():
    """Test that is_valid_executable returns True for executable files."""

    # Create an executable file
    tmp_file = tempfile.NamedTemporaryFile()
    st = os.stat(tmp_file.name)
    os.chmod(tmp_file.name, st.st_mode | stat.S_IXUSR)
    assert ToolPlugin.is_valid_executable(tmp_file.name)


def test_tool_plugin_is_valid_executable_no_exe_flag():
    """
    Test that is_valid_executable returns False for a non-executable file.

    NOTE: any platform which doesn't have executable bits should skip
    this test, since the os.stat call will always say that the file is
    executable
    """

    if sys.platform.startswith('win32'):
        pytest.skip("windows doesn't have executable flags")
    # Create a file
    tmp_file = tempfile.NamedTemporaryFile()
    assert not ToolPlugin.is_valid_executable(tmp_file.name)


def test_tool_plugin_is_valid_executable_nonexistent():
    """Test that is_valid_executable returns False for a nonexistent file."""
    assert not ToolPlugin.is_valid_executable('nonexistent')


def test_tool_plugin_command_exists_valid_win32_fullpath_extension(monkeypatch):
    """
    Test that command_exists works correctly (win32 environment, full path given, .exe appended)

    command_exists should find the file as created.
    """
    # Monkeypatch sys.platform to be win32
    monkeypatch.setattr('sys.platform', lambda: 'win32')

    # Make a temporary directory which will be part of the path
    tmp_dir = tempfile.mkdtemp()

    # Make a temporary executable
    tmp_file = tempfile.NamedTemporaryFile(suffix='.exe', dir=tmp_dir)
    st = os.stat(tmp_file.name)
    os.chmod(tmp_file.name, st.st_mode | stat.S_IXUSR)

    sys.path.insert(0, tmp_dir)

    assert ToolPlugin.command_exists(tmp_file.name)

    # Cleanup
    shutil.rmtree(tmp_dir)


def test_tool_plugin_command_exists_valid_win32_fullpath_different_extension(monkeypatch):
    """
    Test that command_exists works correctly (win32 environment, full path given, non-exe extension).

    command_exists shouldn't try to add .exe and should find the file as provided.
    """
    # Monkeypatch sys.platform to be win32
    monkeypatch.setattr('sys.platform', lambda: 'win32')

    # Make a temporary directory which will be part of the path
    tmp_dir = tempfile.mkdtemp()

    # Make a temporary executable
    tmp_file = tempfile.NamedTemporaryFile(suffix='.bat', dir=tmp_dir)
    st = os.stat(tmp_file.name)
    os.chmod(tmp_file.name, st.st_mode | stat.S_IXUSR)

    sys.path.insert(0, tmp_dir)

    assert ToolPlugin.command_exists(tmp_file.name)

    # Cleanup
    shutil.rmtree(tmp_dir)


def test_tool_plugin_command_exists_valid_win32_fullpath_no_extension(monkeypatch):
    """
    Test that command_exists works correctly (win32 environment, full path given, no extension).

    command_exists shouldn't try to add .exe (because it's a full path)
    """
    # Monkeypatch sys.platform to be win32
    monkeypatch.setattr('sys.platform', lambda: 'win32')

    # Make a temporary directory which will be part of the path
    tmp_dir = tempfile.mkdtemp()

    # Make a temporary executable
    tmp_file = tempfile.NamedTemporaryFile(dir=tmp_dir)
    st = os.stat(tmp_file.name)
    os.chmod(tmp_file.name, st.st_mode | stat.S_IXUSR)

    sys.path.insert(0, tmp_dir)

    assert ToolPlugin.command_exists(tmp_file.name)

    # Cleanup
    shutil.rmtree(tmp_dir)
