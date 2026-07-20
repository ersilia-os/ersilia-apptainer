from contextlib import contextmanager

from loguru import logger as _loguru
from rich.console import Console
from rich.logging import RichHandler


class Logger:
    """
    Two-track logger.

      * verbose mode -> the full loguru/Rich debug stream (every info/debug
        line, rich tracebacks). Best for diagnosing problems.
      * quiet mode   -> a clean user-facing track: an animated spinner for each
        long-running phase plus concise ✓/!/✗ milestone lines, so the user
        always knows the program is working and never faces a silent,
        seemingly-stuck terminal.

    Errors, warnings and success milestones are shown in BOTH modes — only the
    detailed info/debug stream is suppressed when quiet.
    """

    def __init__(self):
        _loguru.remove()
        self.console = Console()
        self._sink_id = None
        self._verbose = False
        self.set_verbosity(False)

    def set_verbosity(self, verbose: bool):
        self._verbose = bool(verbose)
        if self._sink_id is not None:
            try:
                _loguru.remove(self._sink_id)
            except Exception:
                pass
            self._sink_id = None
        if self._verbose:
            handler = RichHandler(
                rich_tracebacks=True,
                markup=True,
                show_path=False,
                log_time_format="%H:%M:%S",
            )
            self._sink_id = _loguru.add(handler, format="{message}", colorize=True)

    # ── detailed stream (verbose only) ────────────────────────────────────────
    def debug(self, msg): _loguru.debug(msg)
    def info(self, msg): _loguru.info(msg)

    # ── user-facing milestones (always visible) ───────────────────────────────
    def success(self, msg):
        if self._verbose:
            _loguru.success(msg)
        else:
            self.console.print(f"[bold green]✓[/] {msg}")

    def warning(self, msg):
        if self._verbose:
            _loguru.warning(msg)
        else:
            self.console.print(f"[bold yellow]![/] {msg}")

    def error(self, msg):
        if self._verbose:
            _loguru.error(msg)
        else:
            self.console.print(f"[bold red]✗[/] {msg}")

    # ── spinner for long-running phases ───────────────────────────────────────
    @contextmanager
    def status(self, message: str):
        """
        Show an animated spinner with `message` while the wrapped block runs
        (quiet mode). In verbose mode a spinner would fight the debug stream,
        so the message is emitted as an info line and the block runs plainly.
        """
        if self._verbose:
            self.info(message)
            yield
        else:
            with self.console.status(f"[bold cyan]{message}", spinner="dots"):
                yield


logger = Logger()
