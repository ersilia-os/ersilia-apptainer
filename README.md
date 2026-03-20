# Ersilia-apptainer

Ersilia-apptainer is a command-line tool for running and creating Ersilia containerized models on high-performance computing (HPC) systems using Apptainer/Singularity. It provides a simple, reproducible, file-based workflow in environments where Docker is not available or permitted, such as shared HPC clusters.

- **`create`** — build a portable `.sif` image from any Ersilia DockerHub model
- **`run`** — execute an Ersilia model from an existing `.sif` container

## Installation

### System requirements

- **Singularity / Apptainer** — must be available in your `PATH` (required for both `run` and `create`)
- Python **≥ 3.9**

> ⚠️ Apptainer/Singularity is a system dependency and must be installed separately.
> On most HPC systems it is provided via environment modules (e.g. `module load singularity`).

Verify it is available:

```bash
singularity --version   # or: apptainer --version
```

### Python environment

```bash
conda create -n ersilia_apptainer python=3.9
conda activate ersilia_apptainer
pip install git+https://github.com/ersilia-os/ersilia-apptainer.git
```

For development:

```bash
git clone https://github.com/ersilia-os/ersilia-apptainer.git
cd ersilia-apptainer
pip install -e .
```

## Usage

### `ersilia_apptainer create` — build a `.sif` image

Pull an Ersilia model from DockerHub and convert it to a portable Singularity image.

```bash
ersilia_apptainer create \
  --model eos2xeq \
  --version v1.0.0 \
  --output-dir /data/sif_images
```

This produces `/data/sif_images/eos2xeq_v1.sif`.
Only the **major** version number is used in the output filename (`v1.0.0` → `_v1`).

| Argument | Required | Description |
|---|---|---|
| `--model` | yes | Ersilia model ID (e.g. `eos2xeq`) |
| `--version` | yes | DockerHub tag (e.g. `v1.0.0`) |
| `--output-dir` | no | Directory for the `.sif` file (default: current directory) |
| `--verbose` | no | Enable debug logging |

Under the hood, `create` generates an Apptainer definition file and runs `singularity build`. The definition moves model bundles to `/opt/ersilia` so the image is readable by any user on shared filesystems.

---

### `ersilia_apptainer run` — execute a model

Run predictions from an existing `.sif` image against an input CSV file.

```bash
ersilia_apptainer run \
  --sif eos2xeq_v1.sif \
  --input compounds.csv \
  --output predictions.csv
```

| Argument | Required | Description |
|---|---|---|
| `--sif` | yes | Path to the `.sif` image |
| `--input` | yes | Input CSV file (first column: SMILES) |
| `--output` | yes | Output CSV path |
| `--verbose` | no | Enable debug logging |

#### Execution model

Input, output, and `.sif` files can live **anywhere on the filesystem** — they do not need to be in the same directory. The runner resolves all paths to absolute form and bind-mounts each parent directory into the container at the same path, so paths are identical inside and outside the container.

```
Host path                        Container (same path)
---------------------------------   ---------------------------------
/data/inputs/compounds.csv  ──▶   /data/inputs/compounds.csv
/results/predictions.csv    ◀──   /results/predictions.csv
```

The model entrypoint (`main.py`) is auto-discovered inside the container at:

```
/opt/ersilia/bundles/<bundle>/model/framework/code/main.py
```

After execution, the tool validates that the output row count matches the input, then prepends two columns to the output CSV to match the standard Ersilia output format:

| Column | Description |
|--------|-------------|
| `key`  | MD5 hash of the input SMILES string |
| `input` | Original SMILES string |

---

### End-to-end example

```bash
# 1. Build the image (once)
ersilia_apptainer create --model eos2xeq --version v1.0.0

# 2. Run predictions
ersilia_apptainer run \
  --sif eos2xeq_v1.sif \
  --input compounds.csv \
  --output predictions.csv
```

## About the Ersilia Open Source Initiative

The [Ersilia Open Source Initiative](https://ersilia.io) is a tech-nonprofit organization fueling sustainable research in the Global South. Ersilia's main asset is the [Ersilia Model Hub](https://github.com/ersilia-os/ersilia), an open-source repository of AI/ML models for antimicrobial drug discovery.

![Ersilia Logo](assets/Ersilia_Brand.png)
