"""Ejecuta un trabajo del alumno bajo límites y devuelve lo que produjo.

El proceso que llama corre como root. Cada trabajo recibe el uid de su ranura
(`slot_uid`), un directorio de trabajo nuevo y los límites de `launcher.py`. Aquí
se vigilan los límites que el kernel no aplica solo: reloj, memoria total,
tamaño del directorio y volumen de salida. Al terminar se matan todos los procesos de ese
uid y se borran sus archivos, también los de /scratch, /tmp, /var/tmp y /dev/shm.
"""

import contextlib
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

APP = Path(__file__).resolve().parent
SCRATCH_ROOT = Path(os.environ.get("QG_SCRATCH", "/scratch"))
UID_BASE = 20000
SHARED_DIRS = ("/scratch", "/tmp", "/var/tmp", "/dev/shm")
PAGE = os.sysconf("SC_PAGE_SIZE")
POLL_S = 0.02
DISK_POLL_S = 0.1
MAX_ENTRIES = 5000
REPORT_CAP = 2**20


@dataclass(frozen=True)
class Limits:
    wall_s: float = 10.0
    mem_mb: int = 512
    scratch_mb: int = 64
    out_bytes: int = 64 * 1024
    nproc: int = 64
    file_mb: int = 16


@dataclass
class Outcome:
    output: str
    report: bytes
    killed: str | None
    peak_mb: int
    ms: int


def _pids_of(uid: int) -> Iterator[int]:
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            if os.stat(f"/proc/{name}").st_uid == uid:
                yield int(name)
        except OSError:
            continue


def _rss_bytes(uid: int) -> int:
    """Memoria residente de los procesos de `uid`."""
    total = 0
    for pid in _pids_of(uid):
        try:
            with open(f"/proc/{pid}/statm") as f:
                total += int(f.read().split()[1]) * PAGE
        except (OSError, ValueError, IndexError):
            continue
    return total


def kill_uid(uid: int) -> None:
    """Mata todos los procesos de `uid`, también los que hicieron setsid."""
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        pids = list(_pids_of(uid))
        if not pids:
            return
        for pid in pids:
            with contextlib.suppress(OSError):
                os.kill(pid, signal.SIGKILL)
        time.sleep(0.01)


def _tree_bytes(root: Path) -> int | None:
    """Bytes en disco bajo `root`; None si hay demasiadas entradas."""
    total = 0
    seen = 0
    stack = [str(root)]
    while stack:
        try:
            with os.scandir(stack.pop()) as it:
                for e in it:
                    seen += 1
                    if seen > MAX_ENTRIES:
                        return None
                    st = e.stat(follow_symlinks=False)
                    total += st.st_blocks * 512
                    if e.is_dir(follow_symlinks=False):
                        stack.append(e.path)
        except OSError:
            continue
    return total


def _remove_owned(uid: int, root: str) -> None:
    """Borra de `root` lo que pertenece a `uid`, sin seguir enlaces."""
    for dirpath, dirnames, filenames in os.walk(root, topdown=False, followlinks=False):
        for name in filenames + dirnames:
            path = os.path.join(dirpath, name)
            try:
                if os.lstat(path).st_uid != uid:
                    continue
                if os.path.isdir(path) and not os.path.islink(path):
                    os.rmdir(path)
                else:
                    os.unlink(path)
            except OSError:
                continue


def _drain(fd: int, cap: int, box: bytearray, over: threading.Event) -> None:
    while True:
        try:
            chunk = os.read(fd, 65536)
        except OSError:
            break
        if not chunk:
            break
        room = cap - len(box)
        box.extend(chunk[:room])
        if len(chunk) > room:
            over.set()


class _Scan(threading.Thread):
    """Vigila memoria y disco en su propio hilo.

    Recorrer /proc puede tardar segundos mientras un fork bomb crea procesos; así
    el reloj de `run_job` sigue su curso. `killed` se escribe antes de `tripped`.
    """

    def __init__(self, uid: int, work: Path, limits: Limits) -> None:
        super().__init__(daemon=True)
        self.uid, self.work = uid, work
        self.mem_cap = limits.mem_mb * 2**20
        self.disk_cap = limits.scratch_mb * 2**20
        self.peak = 0
        self.killed: str | None = None
        self.tripped = threading.Event()
        self.stopped = threading.Event()

    def run(self) -> None:
        next_disk = 0.0
        while not self.stopped.wait(POLL_S):
            rss = _rss_bytes(self.uid)
            self.peak = max(self.peak, rss)
            reason = "memory" if rss > self.mem_cap else None
            if reason is None and time.monotonic() >= next_disk:
                next_disk = time.monotonic() + DISK_POLL_S
                used = _tree_bytes(self.work)
                if used is None or used > self.disk_cap:
                    reason = "disk"
            if reason:
                self.killed = reason
                self.tripped.set()
                return


def slot_uid(slot: int) -> int:
    return UID_BASE + slot


def run_job(
    slot: int,
    files: Mapping[str, str],
    argv: Sequence[str],
    limits: Limits,
    env: Mapping[str, str],
    report: bool = False,
) -> Outcome:
    """Ejecuta `argv` con `files` escritos en un directorio nuevo.

    `argv` y los valores de `env` pueden usar `{dir}`, la ruta del directorio.
    Con `report=True` el hijo hereda un pipe, cuyo número va en QG_REPORT_FD.
    La salida estándar y la de errores van juntas, en el orden en que se escribieron.
    `killed` es `time`, `memory`, `disk` u `output` si el trabajo pasó ese límite.
    """
    uid = slot_uid(slot)
    start = time.monotonic()
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(dir=SCRATCH_ROOT))
    try:
        os.chown(work, uid, uid)
        os.chmod(work, 0o700)
        for name, text in files.items():
            path = work / name
            path.write_text(text, encoding="utf-8")
            os.chown(path, uid, uid)

        child_env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": str(work),
            "TMPDIR": str(work),
            "MPLCONFIGDIR": str(work),
            "LANG": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "PYTHONUNBUFFERED": "1",
            "PYTHONPATH": str(APP),
            "MPLBACKEND": "Agg",
            "OMP_NUM_THREADS": "2",
            "OPENBLAS_NUM_THREADS": "2",
            **{k: v.replace("{dir}", str(work)) for k, v in env.items()},
        }
        cmd = [a.replace("{dir}", str(work)) for a in argv]
        launch = [
            sys.executable,
            "-S",
            str(APP / "launcher.py"),
            str(uid),
            str(int(limits.wall_s) + 2),
            str(limits.mem_mb * 2**20),
            str(limits.file_mb * 2**20),
            str(limits.nproc),
            "--",
            *cmd,
        ]
        pass_fds: tuple[int, ...] = ()
        rep_r = rep_w = None
        if report:
            rep_r, rep_w = os.pipe()
            child_env["QG_REPORT_FD"] = str(rep_w)
            pass_fds = (rep_w,)

        proc = subprocess.Popen(
            launch,
            cwd=work,
            env=child_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            pass_fds=pass_fds,
        )
        if rep_w is not None:
            os.close(rep_w)
        assert proc.stdout is not None

        over = threading.Event()
        out, rep = bytearray(), bytearray()
        readers = [
            threading.Thread(
                target=_drain, args=(proc.stdout.fileno(), limits.out_bytes, out, over)
            ),
        ]
        if rep_r is not None:
            readers.append(threading.Thread(target=_drain, args=(rep_r, REPORT_CAP, rep, over)))
        for t in readers:
            t.start()

        scan = _Scan(uid, work, limits)
        scan.start()
        killed: str | None = None
        deadline = start + limits.wall_s
        while proc.poll() is None:
            if over.is_set():
                killed = "output"
            elif scan.tripped.is_set():
                killed = scan.killed
            elif time.monotonic() > deadline:
                killed = "time"
            if killed:
                break
            time.sleep(POLL_S)

        with contextlib.suppress(OSError):
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        scan.stopped.set()
        kill_uid(uid)
        scan.join(timeout=2)
        for t in readers:
            t.join(timeout=2)
        proc.stdout.close()
        if rep_r is not None:
            os.close(rep_r)
        return Outcome(
            output=out.decode("utf-8", "replace"),
            report=bytes(rep),
            killed=killed,
            peak_mb=round(scan.peak / 2**20),
            ms=round((time.monotonic() - start) * 1000),
        )
    finally:
        kill_uid(uid)
        shutil.rmtree(work, ignore_errors=True)
        for d in SHARED_DIRS:
            _remove_owned(uid, d)
