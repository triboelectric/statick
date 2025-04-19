# statick-action

![Statick](https://github.com/triboelectric/statick/workflows/self-test.yml/badge.svg?branch=525-move-statick-action-this-this-main-repo)

Improve your code quality by running dozens of the most popular and effective static code analysis
tools at once from one simple action.
The supported tools cover many popular programming, scripting, and documentation languages.

This **GitHub Action** uses the **[Statick](https://github.com/triboelectric/statick)** static code analysis tool.

The action inputs mirror the command line arguments for the CLI version of
Statick, and much more detail about the powerful Statick configuration options is
available in the README of the above repository.

## Inputs

### `check`

Any discovered Statick issue fails the action. Default `true`.

Setting this input to `false` may be useful to allow the workflow to work through all steps while debugging.

### `config`

The Statick config file to use. Default: `config.yaml`.

### `log_level`

The Statick log level to use. Default: `INFO`.

### `output_path`

Where to write Statick logs. Default: `/tmp/statick_output`.

### `package_path`

Where Statick should look for files to perform static analysis on. Default: `.`

### `profile`

The Statick profile file to use. Default: `profile.yaml`.

### `timings`

Output timing information to stdout. Default `false`.

### `level`

Scan all packages using this level. Overrides all levels set from the profile.

### `user_paths`

Where to look for user-provided Statick configuration. Default: empty string.

## Example usage

The minimal use of `statick-action`, presuming some code is present in the workflow workspace is:

```shell
uses: actions/statick-action
```

More advanced usage, including use of specific profiles, configurations,
and user-specified resources can be viewed in the
[self-test workflow](https://github.com/triboelectric/statick/blob/main/.github/workflows/self-test.yml)
in this repository.
