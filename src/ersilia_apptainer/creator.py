import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from ersilia_apptainer.logger import logger

DEF_TEMPLATE = """\
Bootstrap: docker
From: ersiliaos/{model_id}:{version}

%post
    # Move the bundles to a world-readable location
    mkdir -p /opt/ersilia
    mv /root/bundles /opt/ersilia/bundles
    mv /root/model /opt/ersilia/model

    # Ensure every user has read/execute permissions
    chmod -R 755 /opt/ersilia

    # Optional: Update environment variables if the model expects them
    export ERSILIA_PATH=/opt/ersilia

%environment
    export ERSILIA_PATH=/opt/ersilia
"""


def _parse_major_version(version: str) -> str:
    """
    Extract major version from a version string.
    Examples:
      'v2.3.2' -> 'v2'
      'v1.0.0' -> 'v1'
      '2.3.2'  -> 'v2'
    """
    # Strip leading 'v' for parsing, then re-add
    stripped = version.lstrip("v")
    match = re.match(r"^(\d+)", stripped)
    if not match:
        raise ValueError(f"Cannot parse major version from: {version!r}")
    return f"v{match.group(1)}"


class ErsiliaApptainerCreator:
    """
    Builds an Apptainer (.sif) image from an Ersilia Docker image on DockerHub.
    """

    def __init__(self, model: str, version: str, output_dir: str = "."):
        self.model = model
        self.version = version
        self.output_dir = Path(output_dir).expanduser().resolve()

        if not self.output_dir.exists():
            raise FileNotFoundError(f"Output directory does not exist: {self.output_dir}")
        if not os.access(self.output_dir, os.W_OK):
            raise PermissionError(f"Output directory is not writable: {self.output_dir}")

        self._check_singularity()

    def _check_singularity(self):
        if shutil.which("singularity") is None:
            raise RuntimeError(
                "Singularity is not available in PATH. "
                "Please install Singularity or load the appropriate module."
            )

    @property
    def sif_name(self) -> str:
        major = _parse_major_version(self.version)
        return f"{self.model}_{major}.sif"

    @property
    def sif_path(self) -> Path:
        return self.output_dir / self.sif_name

    def create(self) -> str:
        """
        Build the .sif image and return its path.
        """
        major = _parse_major_version(self.version)
        logger.info(f"Building SIF image for model [bold]{self.model}[/bold] version [bold]{self.version}[/bold] (major: {major})")
        logger.info(f"Docker source: [cyan]ersiliaos/{self.model}:{self.version}[/cyan]")
        logger.info(f"Output file:   [cyan]{self.sif_path}[/cyan]")

        def_content = DEF_TEMPLATE.format(model_id=self.model, version=self.version)

        with tempfile.TemporaryDirectory() as tmpdir:
            def_file = Path(tmpdir) / f"{self.model}.def"
            def_file.write_text(def_content)

            logger.debug(f"Definition file written to: {def_file}")

            cmd = [
                "singularity",
                "build",
                str(self.sif_path),
                str(def_file),
            ]

            logger.info("Running singularity build — this may take a few minutes...")

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            if result.stdout:
                for line in result.stdout.splitlines():
                    logger.debug(line)

            if result.returncode != 0:
                logger.error("singularity build failed")
                raise RuntimeError(
                    f"singularity build failed (exit {result.returncode}).\n"
                    f"{result.stdout.strip()}"
                )

        logger.success(f"SIF image created successfully: {self.sif_path}")
        return str(self.sif_path)
