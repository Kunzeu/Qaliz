"""Vigila la carpeta de arcdps y sube logs nuevos a Discord automáticamente."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

import aiohttp
import discord

from utils.gw2_log_analysis import upload_log_bytes

logger = logging.getLogger(__name__)

LOG_EXTENSIONS = {".evtc", ".zevtc"}
DEFAULT_ARCDPS_DIR = os.path.join(
    os.path.expanduser("~"),
    "Documents",
    "Guild Wars 2",
    "addons",
    "arcdps",
    "arcdps.cbtlogs",
)
STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
STATE_FILE = os.path.join(STATE_DIR, "log_autoupload_state.dat")


def resolve_log_dir(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    expanded = os.path.normpath(os.path.expandvars(os.path.expanduser(path.strip())))
    return expanded if os.path.isdir(expanded) else None


def iter_log_files(log_dir: str) -> list[str]:
    found: list[str] = []
    for root, _dirs, files in os.walk(log_dir):
        for name in files:
            lower = name.lower()
            if any(lower.endswith(ext) for ext in LOG_EXTENSIONS):
                found.append(os.path.join(root, name))
    return found


def file_fingerprint(path: str) -> Optional[dict]:
    try:
        stat = os.stat(path)
    except OSError:
        return None
    return {"mtime": stat.st_mtime, "size": stat.st_size}


@dataclass
class AutouploadStats:
    last_upload_at: Optional[datetime] = None
    last_upload_boss: str = ""
    last_upload_permalink: str = ""
    last_error: str = ""
    uploads_ok: int = 0
    uploads_skipped: int = 0
    uploads_failed: int = 0
    pending: int = 0


@dataclass
class LogAutouploader:
    bot: discord.Client
    log_dir: str
    poll_seconds: float = 8.0
    only_success: bool = True
    min_players: int = 4
    max_file_size: int = 50 * 1024 * 1024
    user_token: Optional[str] = None
    analyze_fn: Optional[Callable] = None
    get_targets_fn: Optional[Callable] = None

    _task: Optional[asyncio.Task] = field(default=None, init=False, repr=False)
    _processed: dict[str, dict] = field(default_factory=dict, init=False)
    _pending: set[str] = field(default_factory=set, init=False)
    _stats: AutouploadStats = field(default_factory=AutouploadStats, init=False)
    _session: Optional[aiohttp.ClientSession] = field(default=None, init=False, repr=False)

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def __post_init__(self) -> None:
        os.makedirs(STATE_DIR, exist_ok=True)
        self._load_state()

    @property
    def stats(self) -> AutouploadStats:
        return self._stats

    def _load_state(self) -> None:
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._processed = data.get("processed", {})
        except (FileNotFoundError, json.JSONDecodeError):
            self._processed = {}

    def _save_state(self) -> None:
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({"processed": self._processed}, f, indent=2)
        except OSError as exc:
            logger.warning("No se pudo guardar estado autoupload: %s", exc)

    def _is_processed(self, path: str, fp: dict) -> bool:
        prev = self._processed.get(path)
        return bool(prev and prev.get("mtime") == fp["mtime"] and prev.get("size") == fp["size"])

    def _mark_processed(self, path: str, fp: dict, *, permalink: str = "", skipped: bool = False) -> None:
        self._processed[path] = {
            **fp,
            "permalink": permalink,
            "skipped": skipped,
            "at": datetime.utcnow().isoformat(),
        }
        self._save_state()

    def baseline_existing_files(self) -> int:
        """Marca logs existentes como vistos sin subirlos (solo la primera vez)."""
        if self._processed:
            return 0
        count = 0
        for path in iter_log_files(self.log_dir):
            fp = file_fingerprint(path)
            if fp:
                self._mark_processed(path, fp, skipped=True)
                count += 1
        logger.info("Autoupload: baseline de %s archivos existentes", count)
        return count

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self.baseline_existing_files()
        self._session = aiohttp.ClientSession()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Autoupload iniciado — vigilando %s", self.log_dir)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _run_loop(self) -> None:
        while True:
            try:
                await self._scan_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Error en scan autoupload")
            await asyncio.sleep(self.poll_seconds)

    async def _scan_once(self) -> None:
        for path in iter_log_files(self.log_dir):
            if path in self._pending:
                continue
            fp = file_fingerprint(path)
            if not fp or self._is_processed(path, fp):
                continue
            if fp["size"] > self.max_file_size:
                self._mark_processed(path, fp, skipped=True)
                self._stats.uploads_skipped += 1
                continue
            if not await self._wait_for_stable(path):
                continue
            fp = file_fingerprint(path)
            if not fp or self._is_processed(path, fp):
                continue
            self._pending.add(path)
            self._stats.pending = len(self._pending)
            try:
                await self._process_file(path, fp)
            finally:
                self._pending.discard(path)
                self._stats.pending = len(self._pending)

    async def _wait_for_stable(self, path: str, checks: int = 3, interval: float = 1.5) -> bool:
        last_size = -1
        stable = 0
        for _ in range(20):
            if not os.path.isfile(path):
                return False
            size = os.path.getsize(path)
            if size > 0 and size == last_size:
                stable += 1
                if stable >= checks:
                    return True
            else:
                stable = 0
            last_size = size
            await asyncio.sleep(interval)
        return False

    async def _process_file(self, path: str, fp: dict) -> None:
        if not self._session or not self.analyze_fn or not self.get_targets_fn:
            return

        filename = os.path.basename(path)
        try:
            with open(path, "rb") as f:
                file_bytes = f.read()
        except OSError as exc:
            self._stats.uploads_failed += 1
            self._stats.last_error = str(exc)
            logger.error("No se pudo leer %s: %s", path, exc)
            return

        data, err = await upload_log_bytes(
            self._session,
            file_bytes,
            filename,
            user_token=self.user_token,
        )
        if err or not data:
            self._stats.uploads_failed += 1
            self._stats.last_error = err or "upload failed"
            logger.warning("Fallo subiendo %s: %s", filename, err)
            if err and "Rate limit" in err:
                await asyncio.sleep(60)
            return

        encounter = data.get("encounter") or {}
        n_players = int(encounter.get("numberOfPlayers") or 0)
        success = bool(encounter.get("success"))
        boss = encounter.get("boss") or encounter.get("target") or "?"

        targets = await self.get_targets_fn()
        guild_only_success = {t["guild_id"]: t.get("only_success", self.only_success) for t in targets}

        skip_post = False
        if n_players < self.min_players:
            skip_post = True
        elif self.only_success and not success:
            skip_post = True

        if skip_post:
            self._mark_processed(path, fp, permalink=data.get("permalink", ""), skipped=True)
            self._stats.uploads_skipped += 1
            logger.info("Autoupload omitido %s (%s, %s jugadores)", filename, boss, n_players)
            return

        posted = 0
        for target in targets:
            gid = target["guild_id"]
            if guild_only_success.get(gid, self.only_success) and not success:
                continue
            channel_id = int(target["channel_id"])
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await self.bot.fetch_channel(channel_id)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    logger.warning("Canal autoupload %s no accesible", channel_id)
                    continue
            try:
                guild = getattr(channel, "guild", None)
                target_embed = await self.analyze_fn(self._session, data, guild)
                await channel.send(embed=target_embed)
                posted += 1
            except discord.HTTPException as exc:
                logger.error("Error enviando autoupload a %s: %s", channel_id, exc)

        self._mark_processed(path, fp, permalink=data.get("permalink", ""))
        if posted:
            self._stats.uploads_ok += 1
            self._stats.last_upload_at = datetime.utcnow()
            self._stats.last_upload_boss = str(boss)
            self._stats.last_upload_permalink = data.get("permalink", "")
            self._stats.last_error = ""
            logger.info("Autoupload OK %s → %s canal(es)", filename, posted)
        else:
            self._stats.uploads_failed += 1
            self._stats.last_error = "No se pudo publicar en ningún canal configurado"
