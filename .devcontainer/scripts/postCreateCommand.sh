#!/usr/bin/env bash

REPO_NAME=statick
HOME=/opt

echo "Installing 'dev' command..."
# The `ln -s` is what allows the commands to be run in Bash just by using the command name.
# So instead of running $HOME/$REPO_NAME/.devcontainer/scripts/dev.sh,
# the user can just run dev from anywhere in the DevContainer.
ln -s $HOME/$REPO_NAME/.devcontainer/scripts/dev.sh /usr/local/bin/dev

# Uncomment this line if necessary.
# git config --global --add safe.directory $HOME/$REPO_NAME

bash $HOME/$REPO_NAME/.devcontainer/scripts/postCreateCommandUser.sh
