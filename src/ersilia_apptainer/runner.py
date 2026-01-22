import os
import shutil
import subprocess
from pathlib import Path

from loguru import logger as _loguru
from rich.console import Console
from rich.logging import RichHandler


class Logger:
    def __init__(self):
        _loguru.remove()
        self.console = Console()
        self._sink_id = None
        self.set_verbosity(True)

    def set_verbosity(self, verbose):
        if self._sink_id is not None:
            try:
                _loguru.remove(self._sink_id)
            except Exception:
                pass
            self._sink_id = None
        if verbose:
            handler = RichHandler(rich_tracebacks=True, markup=True, show_path=False, log_time_format="%H:%M:%S")
            self._sink_id = _loguru.add(handler, format="{message}", colorize=True)

    def debug(self, msg): _loguru.debug(msg)
    def info(self, msg): _loguru.info(msg)
    def warning(self, msg): _loguru.warning(msg)
    def error(self, msg): _loguru.error(msg)
    def success(self, msg): _loguru.success(msg)

logger= Logger()

class ErsiliaApptainer:
    """
    Wrapper for executing ersilia.sif containers
    """
    def __init__(self, container:str=None, input:str=None, output:str='output.csv'):
        self.container=container
        self.input=input
        self.output= output
        self.main_py=None
        
        self._check_apptainer()
        self._find_main()

    @property
    def container(self):
        return self._container
        

    @container.setter
    def container(self, value:str):
        path = Path(value).expanduser().resolve()

        if not path.exists():
            raise FileNotFoundError(f"Container not found: {path}")
        if path.suffix.lower() != ".sif":
            raise ValueError(f"Container must be a .sif file: {path}")

        self._container = str(path)

    @property
    def input(self) -> str:
        return self._input

    @input.setter
    def input(self, value: str):
        path = Path(value).expanduser().resolve()

        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        if not path.is_file():
            raise ValueError(f"Input path is not a file: {path}")

        self._input = str(path)

    @property
    def output(self) -> str:
        return self._output


    @output.setter
    def output(self, value: str):
        path = Path(value).expanduser()

        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()

        parent = path.parent
        if not parent.exists():
            raise FileNotFoundError(f"Output directory does not exist: {parent}")
        if not os.access(parent, os.W_OK):
            raise PermissionError(f"Output directory is not writable: {parent}")

        self._output = str(path)

    def _check_apptainer(self):
        if shutil.which("singularity") is None:
            raise RuntimeError(
                "Singularity is not available in PATH. "
                "Please install Singularity or load the appropriate module."
            )
        
    def _find_main(self):
        """
        Locate the model execution entrypoint (main.py) inside the container.
        """
        cmd=[
            "singularity",
            "exec",
            "--pwd", "/",
            self.container,
            "sh",
            "-lc",
            "find /opt/ersilia/bundles -type f -path '*/model/framework/code/main.py' 2>/dev/null",
        ]
        result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to inspect container:\n{result.stderr.strip()}"
            )

        matches = [line.strip() for line in result.stdout.splitlines() if line.strip()]

        if not matches:
            raise RuntimeError(
                "Could not locate model entrypoint (main.py) inside the container."
            )

        if len(matches) > 1:
            raise RuntimeError(
                "Multiple model entrypoints found inside the container:\n"
                + "\n".join(matches)
            )

        self.main_py = matches[0]
        self.bundle_root = str(Path(self.main_py).parents[4])   

        logger.info(f"Model entrypoint found: {self.main_py}")
    
    
    def _count_lines(self, path: str) -> int:
        with open(path, "r") as f:
            return sum(1 for line in f if line.strip())
    
    def _check_output(self):
        """
        Docstring for _check_output
        
        :param self: Description
        """
        input_lines = self._count_lines(self.input)
        output_lines = self._count_lines(self.output)

        logger.info(f"Input lines: {input_lines}")
        logger.info(f"Output lines: {output_lines}")

        if input_lines != output_lines:
            logger.error(
                "Output validation failed: number of output lines "
                "does not match number of input lines"
            )
            raise RuntimeError(
                f"Line count mismatch: input={input_lines}, output={output_lines}"
            )

        logger.success("Output validation passed")
   
    def run(self):
        """
        Execute the Ersilia model inside the Apptainer container
        """
        cwd = Path.cwd().resolve()

        input_name= Path(self.input).name
        output_name= Path(self.output).name
        
        container_input= f"/workspace/{input_name}"
        container_output = f"/workspace/{output_name}"

        cmd = [
            "singularity",
            "exec",
            "--pwd", "/",
            "--bind", f"{cwd}:/workspace",
            self.container,
            "python",
            self.main_py,
            container_input,
            container_output,  
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.stdout:
            logger.info(result.stdout.strip())

        if result.returncode != 0:
            logger.error("Model execution failed")
            if result.stderr:
                logger.error(result.stderr.strip())
            raise RuntimeError("Ersilia model execution failed")

        logger.success(f"Model execution completed successfully")
        logger.info(f"Output written to: {self.output}")

        self._check_output()