FROM ubuntu:24.04

LABEL "name"="Statick"
LABEL "version"="0.12.0"
LABEL "repository"="https://github.com/triboelectric/statick.git"
LABEL "homepage"="https://github.com/triboelectric/statick"
LABEL "maintainer"="Thomas Denewiler <tdenewiler@gmail.com>"

ENV DEBIAN_FRONTEND=noninteractive

# Version pinning may be added in the future, but ignore for now.
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cccc \
    chktex \
    clang \
    clang-18 \
    clang-format \
    clang-format-18 \
    clang-tidy \
    clang-tidy-18 \
    cmake \
    cppcheck \
    curl \
    file \
    findbugs \
    flawfinder \
    git \
    lacheck \
    libomp-dev \
    libpcre3-dev \
    libperl-critic-perl \
    libxml2 \
    libxml2-utils \
    maven \
    python3-pip \
    python3-venv \
    shellcheck \
    uncrustify \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    . $HOME/.local/bin/env && \
    uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install statick[docs,test]

# Statick npm tools.
# Newer version is installed from non-apt source due to SSL library compatibility issues.

# Version pinning may be added in the future, but ignore for now.
# hadolint ignore=DL3008,DL3016
RUN curl -sL https://deb.nodesource.com/setup_20.x -o nodesource_setup.sh && \
    bash nodesource_setup.sh && \
    apt-get update && apt-get install -y --no-install-recommends nodejs && rm -rf /var/lib/apt/lists/* && \
    npm config set prefix -g /usr && \
    npm install -g dockerfilelint && \
    npm install -g dockerfile_lint && \
    npm install -g prettier && \
    npm install -g eslint && \
    npm install -g --prefix $HOME/.node_modules eslint-plugin-html && \
    npm install -g --prefix $HOME/.node_modules eslint-plugin-prettier && \
    npm install -g --prefix $HOME/.node_modules eslint-config-prettier && \
    npm install -g htmllint-cli && \
    npm install -g markdownlint-cli && \
    npm install -g npm-groovy-lint && \
    npm install -g stylelint && \
    npm install -g stylelint-config-standard && \
    npm install -g json-merger

# Install Hadolint binary
RUN mkdir hadolint-bin && \
    curl -sL -o hadolint "https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-$(uname -s)-$(uname -m)" && \
    chmod +x hadolint && \
    mv hadolint hadolint-bin/.
ENV PATH=./hadolint-bin:$PATH

CMD ["bash"]
