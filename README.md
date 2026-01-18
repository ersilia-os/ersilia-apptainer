# Ersilia-apptainer

Ersilia-apptainer is a command-line tool that enables the execution of Ersilia containerized models on high-performance computing (HPC) systems using Apptainer. It provides a simple, reproducible, file-based workflow to run Ersilia models in environments where Docker is not available or permitted, such as shared HPC clusters. The tool automatically discovers the model entrypoint inside an Apptainer image, executes the model with user-provided input files, and validates the output to ensure correctness.

## Installation

### System requirements

- **Apptainer** (must be available as `apptainer` in your `PATH`)
- Python **≥ 3.9**

> ⚠️ Apptainer is a system dependency and must be installed separately.  
> On many HPC systems, Apptainer is provided via environment modules.

You can verify that Apptainer is available with:

```bash
apptainer --version
```

### Python environment

To get started, create a Conda environment:

```bash
conda create -n ersilia_apptainer python=3.9
conda activate ersilia_apptainer
```

Then install the package using pip:

```bash
pip install git+https://github.com/ersilia-os/ersilia-apptainer.git
```

For development, you can also install it in editable mode:

```bash
git clone https://github.com/ersilia-os/ersilia-apptainer.git
cd ersilia-apptainer
pip install -e .
```

## Usage

Ersilia-apptainer provides a file-based command-line interface for running Ersilia models packaged as Apptainer (`.sif`) images.

Run a model from a directory containing your input file:

```bash
ersilia_apptainer \
  --sif eos3b5e.sif \
  --input input.csv \
  --output output.csv
```

To enable verbose logging:

```bash
ersilia_apptainer \
  --sif eos3b5e.sif \
  --input input.csv \
  --output output.csv \
  --verbose
```

### Execution model

- The current working directory is bind-mounted into the container at `/workspace`
- Input and output files must be located in the current directory
- Containers are executed in isolated mode (`--containall`, `--no-home`)
- No files are written inside the container filesystem

```
Host directory        Container
--------------        ----------
./input.csv     ──▶   /workspace/input.csv
./output.csv    ◀──   /workspace/output.csv
```

## About the Ersilia Open Source Initiative

The [Ersilia Open Source Initiative](https://ersilia.io) is a tech-nonprofit organization fueling sustainable research in the Global South. Ersilia's main asset is the [Ersilia Model Hub](https://github.com/ersilia-os/ersilia), an open-source repository of AI/ML models for antimicrobial drug discovery.

![Ersilia Logo](assets/Ersilia_Brand.png)
