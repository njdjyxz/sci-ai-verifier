# Sandbox image for chemistry skills that use RDKit, such as examples/sar-analysis. It adds
# hash-pinned RDKit and pandas wheels to the verifier's pinned base image; trials still install
# nothing. Build it, then pin the image ID it produces in the local settings (LOCAL-CONFIG.md).
# Run 84e90683's subjects had no RDKit, so every trial of its ring-option claim tried to install
# it and then worked the MCS out by hand: two timed out, and six answered wrongly.
FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea
# RDKit's drawing module links X11, Xext, Xrender and expat, which the slim base lacks: without
# them `from rdkit.Chem.Draw import rdMolDraw2D` fails on libXrender.so.1. Versions are exact,
# and apt checks each package against the signed Debian index. Debian drops superseded
# versions, so a later rebuild may need new pins; the verifier runs the image ID, not this file.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libexpat1=2.8.3-1~deb13u1 libxau6=1:1.0.11-1 libxdmcp6=1:1.1.5-1 libxcb1=1.17.0-2+b1 \
        libx11-data=2:1.8.12-1 libx11-6=2:1.8.12-1 libxext6=2:1.3.4-1+b3 libxrender1=1:0.9.12-1 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check --require-hashes --only-binary=:all: \
        -r /tmp/requirements.txt \
    && pip check \
    && rm /tmp/requirements.txt
