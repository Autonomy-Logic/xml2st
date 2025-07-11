# Use official Ubuntu base image
FROM ubuntu:20.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and Python 3.9, plus devcontainer essentials
RUN apt-get update && \
    apt-get install -y software-properties-common curl git sudo locales && \
    locale-gen en_US.UTF-8 && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.9 python3.9-venv python3-pip && \
    ln -sf /usr/bin/python3.9 /usr/bin/python && \
    python -m pip install --upgrade pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Create user 'dev' with sudo privileges
RUN useradd -ms /bin/bash dev && \
    usermod -aG sudo dev && \
    echo "dev ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set the working directory
WORKDIR /workdir

# Copy the requirements.txt file into the container
COPY requirements.txt .

USER dev

# Garante que o diretório .ssh tenha as permissões corretas
RUN mkdir -p /home/dev/.ssh && \
    chown -R dev:dev /home/dev/.ssh && \
    chmod 700 /home/dev/.ssh


# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the default command
CMD ["python"]
