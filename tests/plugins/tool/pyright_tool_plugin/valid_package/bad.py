#! /usr/bin/env python3

# This is a test file with intentional errors for pyright tool plugin.

def bad_return_value() -> int:
    """Function that returns a string instead of an int."""
    return "This should be an int, not a str"
