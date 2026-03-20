import argparse

from rich_argparse import RichHelpFormatter
from rich.text import Text

from ersilia_apptainer.logger import logger
from ersilia_apptainer.runner import ErsiliaApptainer
from ersilia_apptainer.creator import ErsiliaApptainerCreator

# ── Colour palette ────────────────────────────────────────────────────────────
RichHelpFormatter.styles["argparse.prog"]    = "bold cyan"
RichHelpFormatter.styles["argparse.groups"]  = "bold white"
RichHelpFormatter.styles["argparse.args"]    = "bold green"
RichHelpFormatter.styles["argparse.metavar"] = "italic yellow"
RichHelpFormatter.styles["argparse.syntax"]  = "bold cyan"
RichHelpFormatter.highlights.append(
    r"(?P<argparse_syntax>eos\w+|v\d+\.\d+\.\d+|\.sif|\.csv)"
)

_DESCRIPTION = (
    "[bold cyan]ersilia_apptainer[/] — run and create "
    "[bold]Ersilia[/] Apptainer images for HPC systems.\n\n"
    "[dim]Wraps Singularity to execute or build [italic].sif[/italic] "
    "containers derived from Ersilia DockerHub images.[/dim]"
)

_RUN_DESCRIPTION = (
    "Execute an Ersilia model packaged as an Apptainer [italic].sif[/italic] "
    "image.\n\n[dim]Runs the model inside the container using Singularity "
    "and writes predictions to a CSV file.[/dim]"
)
_RUN_EPILOG = (
    "[bold white]Example:[/]\n"
    "  ersilia_apptainer run \\\n"
    "    [green]--sif[/] eos2xeq_v1.sif \\\n"
    "    [green]--input[/] compounds.csv \\\n"
    "    [green]--output[/] predictions.csv"
)

_CREATE_DESCRIPTION = (
    "Build an Apptainer [italic].sif[/italic] image from an Ersilia "
    "DockerHub image.\n\n[dim]Pulls the Docker image, applies the standard "
    "Ersilia post-install layout, and produces a portable [italic].sif[/italic] "
    "file named [bold]<model>_v<major>.sif[/bold].[/dim]"
)
_CREATE_EPILOG = (
    "[bold white]Example:[/]\n"
    "  ersilia_apptainer create \\\n"
    "    [green]--model[/] eos2xeq \\\n"
    "    [green]--version[/] v1.0.0 \\\n"
    "    [green]--output-dir[/] /data/sif_images\n\n"
    "[dim]This will produce: [bold]/data/sif_images/eos2xeq_v1.sif[/bold][/dim]"
)

_EPILOG = (
    "[bold white]Quick start:[/]\n"
    "  [cyan]ersilia_apptainer create --model eos2xeq --version v1.0.0[/]\n"
    "  [cyan]ersilia_apptainer run --sif eos2xeq_v1.sif --input compounds.csv --output out.csv[/]\n\n"
    "[dim]Use [bold]ersilia_apptainer <command> --help[/bold] for command-specific options.[/dim]"
)


def _fmt(**kwargs) -> RichHelpFormatter:
    """Return a formatter factory pre-configured with our shared kwargs."""
    class _F(RichHelpFormatter):
        def __init__(self, prog):
            super().__init__(prog, max_help_position=36, **kwargs)
    return _F


def _add_verbose(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose/debug logging.",
    )


def build_parser() -> argparse.ArgumentParser:
    fmt = _fmt()

    parser = argparse.ArgumentParser(
        prog="ersilia_apptainer",
        description=_DESCRIPTION,
        epilog=_EPILOG,
        formatter_class=fmt,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── run ──────────────────────────────────────────────────────────────────
    run_parser = subparsers.add_parser(
        "run",
        help="Execute an Ersilia model from an existing .sif container.",
        description=_RUN_DESCRIPTION,
        epilog=_RUN_EPILOG,
        formatter_class=fmt,
    )
    run_parser.add_argument(
        "--sif",
        required=True,
        metavar="PATH",
        help="Path to the Apptainer [italic](.sif)[/italic] image.",
    )
    run_parser.add_argument(
        "--input",
        required=True,
        metavar="PATH",
        help="Path to the input CSV file (first column: SMILES).",
    )
    run_parser.add_argument(
        "--output",
        required=True,
        metavar="PATH",
        help="Path where the output CSV will be written.",
    )
    _add_verbose(run_parser)

    # ── create ───────────────────────────────────────────────────────────────
    create_parser = subparsers.add_parser(
        "create",
        help="Build an Apptainer (.sif) image from an Ersilia DockerHub image.",
        description=_CREATE_DESCRIPTION,
        epilog=_CREATE_EPILOG,
        formatter_class=fmt,
    )
    create_parser.add_argument(
        "--model",
        required=True,
        metavar="MODEL_ID",
        help="Ersilia model identifier (e.g. [bold]eos2xeq[/bold]).",
    )
    create_parser.add_argument(
        "--version",
        required=True,
        metavar="VERSION",
        help=(
            "DockerHub version tag (e.g. [bold]v1.0.0[/bold]). "
            "Only the major part is used in the output filename."
        ),
    )
    create_parser.add_argument(
        "--output-dir",
        default=".",
        metavar="DIR",
        help="Directory where the [italic].sif[/italic] file will be saved. [dim](default: current directory)[/dim]",
    )
    _add_verbose(create_parser)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    logger.set_verbosity(args.verbose)

    if args.command == "run":
        try:
            runner = ErsiliaApptainer(
                container=args.sif,
                input=args.input,
                output=args.output,
            )
            runner.run()
            return 0
        except Exception as e:
            logger.error(str(e))
            return 1

    if args.command == "create":
        try:
            creator = ErsiliaApptainerCreator(
                model=args.model,
                version=args.version,
                output_dir=args.output_dir,
            )
            creator.create()
            return 0
        except Exception as e:
            logger.error(str(e))
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
