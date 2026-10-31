from __future__ import annotations

import os
import secrets
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


def resources() -> Path:
    root = Path(__file__).resolve().parent.parent
    return root if (root / "schemas/event.schema.json").exists() else Path(__file__).parent / "data"


def revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent,
            stderr=subprocess.DEVNULL, timeout=2, text=True,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        # Installed wheels use a source-tree digest, not an invented Git commit.
        import hashlib
        code = b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py")))
        return hashlib.sha1(code).hexdigest()


@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("RBF_DATA_DIR", "artifacts/private")))
    control_token: str = ""
    worker_a_url: str = field(default_factory=lambda: os.getenv("RBF_WORKER_A_URL", ""))
    worker_b_url: str = field(default_factory=lambda: os.getenv("RBF_WORKER_B_URL", ""))
    worker_a_token: str = field(default_factory=lambda: os.getenv("RBF_WORKER_A_TOKEN", ""), repr=False)
    worker_b_token: str = field(default_factory=lambda: os.getenv("RBF_WORKER_B_TOKEN", ""), repr=False)
    aws_config: Path | None = None
    auto_recreate_workers: bool = field(default_factory=lambda: os.getenv("RBF_AUTO_RECREATE_WORKERS", "0") == "1")
    code_revision: str = field(default_factory=revision)

    def prepare(self) -> None:
        self.data_dir = self.data_dir.resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.data_dir.chmod(0o700)
        token_path = self.data_dir / "control-token"
        self.control_token = self.control_token or os.getenv("RBF_CONTROL_TOKEN", "")
        if not self.control_token:
            if token_path.exists():
                self.control_token = token_path.read_text().strip()
            else:
                self.control_token = secrets.token_urlsafe(32)
                fd = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w") as handle:
                    handle.write(self.control_token)
        if len(self.control_token) < 24:
            raise ValueError("RBF_CONTROL_TOKEN must contain at least 24 characters")
        if os.getenv("RBF_AWS_CONFIG"):
            self.aws_config = Path(os.environ["RBF_AWS_CONFIG"]).resolve()
