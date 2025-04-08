"""Discovery plugin to find ROS packages."""

import logging
import os
from functools import reduce
from typing import Any, Optional, Union

import xmltodict

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class RosDiscoveryPlugin(DiscoveryPlugin):
    """Discovery plugin to find ROS packages."""

    def get_name(self) -> str:
        """Get name of discovery type.

        Returns:
            Name of the discovery type.
        """
        return "ros"

    @classmethod
    def deep_get(
        cls,
        dictionary: Union[str, dict[Any, str]],
        keys: str,
        default: str = "",
    ) -> Any:
        """Safe way to check for a value in a nested dict.

        Copied from:



        https://stackoverflow.com/questions/25833613/python-safe-method-to-get-value-of-nested-dictionary

        Args:
            dictionary: The dictionary to search.
            keys: The keys to search for.
            default: The default value if the key is not found.

        Returns:
            The value found or the default value.
        """
        return reduce(
            lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
            keys.split("."),
            dictionary,
        )

    def scan(
        self, package: Package, level: str, exceptions: Optional[Exceptions] = None
    ) -> None:
        """Scan package looking for ROS package files.

        Args:
            package: The package to scan.
            level: The level of scanning.
            exceptions: Optional exceptions to apply.
        """
        cmake_file = os.path.join(package.path, "CMakeLists.txt")
        package_file = os.path.join(package.path, "package.xml")
        ros_version = os.getenv("ROS_VERSION")

        if (
            os.path.isfile(cmake_file)
            and os.path.isfile(package_file)
            and ros_version is not None
        ):
            logging.info("  Package is ROS%s.", ros_version)
            if ros_version == "1":
                package["is_ros1"] = True
            elif ros_version == "2":
                distro = os.getenv("ROS_DISTRO")
                path = os.getenv("PATH")
                if path is not None:
                    for item in path.split(":"):
                        if distro is not None and distro in item:
                            package["cmake_flags"] = (
                                "-DCMAKE_PREFIX_PATH=" + item.rstrip("/bin")
                            )
                package["is_ros2"] = True
        elif os.path.isfile(package_file) and ros_version is not None:
            with open(package_file, encoding="utf8") as fconfig:
                try:
                    output = xmltodict.parse(fconfig.read())
                except (
                    xmltodict.expat.ExpatError,  # pyright: ignore
                    xmltodict.ParsingInterrupted,
                ) as exc:
                    # No valid XML found, so we are not going to find the build type.
                    logging.warning("  Invalid XML in %s: %s", package_file, exc)
                    return
                if self.deep_get(output, "package.export.build_type") == "ament_python":
                    logging.info("  Package is ROS%s.", ros_version)
                    package["is_ros2"] = True
