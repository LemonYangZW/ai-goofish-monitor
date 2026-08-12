import os
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.services.account_state_service import normalize_state_path, to_filesystem_path


@dataclass
class RotationItem:
    value: str
    last_error: Optional[str] = None


class RotationPool:
    def __init__(self, items: List[str], blacklist_ttl: int = 300, name: str = ""):
        self.items = [RotationItem(value=item) for item in items if item]
        self.blacklist_ttl = max(0, int(blacklist_ttl))
        self.name = name or "rotation"
        self._blacklist: Dict[str, float] = {}

    def _cleanup_blacklist(self) -> None:
        now = time.time()
        expired = [key for key, ts in self._blacklist.items() if ts <= now]
        for key in expired:
            self._blacklist.pop(key, None)

    def available_items(self) -> List[RotationItem]:
        self._cleanup_blacklist()
        return [item for item in self.items if item.value not in self._blacklist]

    def pick_random(self) -> Optional[RotationItem]:
        candidates = self.available_items()
        if not candidates:
            return None
        return random.choice(candidates)

    def mark_bad(self, item: Optional[RotationItem], reason: str = "") -> None:
        if not item:
            return
        item.last_error = reason
        if self.blacklist_ttl <= 0:
            return
        self._blacklist[item.value] = time.time() + self.blacklist_ttl


def parse_proxy_pool(value: Optional[str]) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [entry.strip() for entry in str(value).split(",") if entry.strip()]


def load_state_files(state_dir: str) -> List[str]:
    if not state_dir:
        return []
    normalized_dir = normalize_state_path(state_dir)
    fs_state_dir = to_filesystem_path(normalized_dir)
    if not os.path.isdir(fs_state_dir):
        return []
    files = []
    for name in os.listdir(fs_state_dir):
        if name.endswith(".json"):
            files.append(normalize_state_path(f"{normalized_dir}/{name}"))
    return sorted(files)
