"""Custom argument handling.

Enable usage of user-paths argument before parsing other arguments.
"""

import argparse
import logging
import os
from typing import Any


class Args:
    """Custom argument handling.

    Enable usage of user-paths argument before parsing other arguments.
    """

    def __init__(self, name: str) -> None:
        """Initialize arguments.

        Args:
            name: Name of the tool.
        """
        self.pre_parser = argparse.ArgumentParser(description=name, add_help=False)
        user_path_args = {
            "dest": "user_paths",
            "type": str,
            "help": "Comma separated list of paths containing "
            "configuration or plugins",
        }
        self.pre_parser.add_argument("--user-paths", "-u", **user_path_args)  # type: ignore

        self.parser = argparse.ArgumentParser(description=name)
        self.parser.add_argument("--user-paths", "-u", **user_path_args)  # type: ignore

    def get_user_paths(self, args: Any = None) -> list[str]:
        """Get a list of user paths containing config or plugins.

        Args:
            args: Arguments to parse.

        Returns:
            List of user paths.
        """
        user_paths: list[str] = []
        args = self.pre_parser.parse_known_args(args)[0]
        if args.user_paths is not None:
            paths: list[str] = args.user_paths.split(",")
            for path in paths:
                if os.path.exists(path) and os.path.isdir(path):
                    user_paths.append(path)
                else:
                    logging.error("Could not find user path %s!", path)
        return user_paths

    def get_args(self, args: list[str] | None = None) -> argparse.Namespace:
        """Get parsed command-line arguments.

        Args:
            args: Arguments to parse.

        Returns:
            Parsed command-line arguments.
        """
        return self.parser.parse_args(args)
