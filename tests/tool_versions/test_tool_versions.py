"""Unit tests of timing.py."""

import os
import sys

import pytest

from statick_tool.args import Args
from statick_tool.statick import Statick
from statick_tool.tool_version import ToolVersion


@pytest.fixture
def init_statick():
    """Fixture to initialize a Statick instance."""
    args = Args("Statick tool")

    return Statick(args.get_user_paths(["--user-paths", os.path.dirname(__file__)]))


def test_add_version(init_statick):
    """Test adding a ToolVersion instance.

    Expected result: ToolVersion instance added is returned in getter method
    """
    tool_name = "test_tool"
    tool_version = "1.2.3"
    version = ToolVersion(tool_name, tool_version)
    init_statick.add_tool_version(tool_name, tool_version)
    versions = init_statick.get_tool_versions()
    assert version in versions


def test_collect_versions(init_statick):
    """Test collecting all tool versions."""
    args = Args("Statick tool")
    args.parser.add_argument(
        "--path", help="Path of package to scan", default=os.path.dirname(__file__)
    )

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    sys.argv = [
        "--output-directory",
        os.path.dirname(__file__),
        "--path",
        os.path.dirname(__file__),
    ]
    parsed_args = args.get_args(sys.argv)
    path = parsed_args.path
    statick.get_config(parsed_args)

    assert statick.collect_tool_versions(args=parsed_args)
    versions = statick.get_tool_versions()
    # Just make sure we get some number of tools, but don't specify an exact number
    assert len(versions) > 0
