## ------------------------------- Builder Stage ------------------------------ ## 
FROM python:3.14-bookworm AS builder

RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Download the latest installer, install it and then remove it
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod -R 655 /install.sh && /install.sh && rm /install.sh

# Set up the UV environment path correctly
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /src

COPY pyproject.toml .

RUN uv sync --no-cache-dir

## ------------------------------- Production Stage ------------------------------ ##
FROM python:3.14-slim-bookworm AS production

# Update system packages to fix vulnerabilities
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ARG USERNAME=appuser

# The following secrets are available during build time
# RUN --mount=type=secret,id=DB_PASSWORD \
# --mount=type=secret,id=DB_USER \
# --mount=type=secret,id=DB_NAME \
# --mount=type=secret,id=DB_HOST \
# --mount=type=secret,id=ACCESS_TOKEN_SECRET_KEY \
# DB_PASSWORD=/run/secrets/DB_PASSWORD \
# DB_USER=$(cat /run/secrets/DB_USER) \
# DB_NAME=$(cat /run/secrets/DB_NAME) \
# DB_HOST=$(cat /run/secrets/DB_HOST) \
# ACCESS_TOKEN_SECRET_KEY=$(cat /run/secrets/ACCESS_TOKEN_SECRET_KEY)

# RUN --mount=type=secret,id=secret-key,target=secrets.json

RUN useradd --create-home ${USERNAME}
USER ${USERNAME}

# [Optional] Add sudo support. Omit if you don't need to install software after connecting.
#
# RUN apt install -y sudo; \
#     echo ${USERNAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USERNAME}; \
#     chmod 0440 /etc/sudoers.d/${USERNAME}

WORKDIR /usr/app

ADD src src
ADD facr_builder.sh .

COPY --from=builder /src/.venv src/.venv

# Set up environment variables for production
ENV PATH="/usr/app/src/.venv/bin:$PATH"

ENTRYPOINT ["python", "src/facr_builder.py"]