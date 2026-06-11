# engine/ude/storage.py
# All documentation, docstrings, and code comments are strictly in English.

import gzip
import hashlib
from pathlib import Path
from typing import Union, Dict, Optional
from pydantic import BaseModel, Field
from ude.models import ProjectCatalog


def save_compressed_ir(catalog: ProjectCatalog, file_path: Union[str, Path]) -> None:
    """Serializes a ProjectCatalog model into JSON and compresses it on-the-fly using Gzip.

    Args:
        catalog: The ProjectCatalog instance to save.
        file_path: The target file path on disk (usually with a .json.gz extension).
    """
    path = Path(file_path)
    # Ensure parent directories exist
    path.parent.mkdir(parents=True, exist_ok=True)

    # Serialize to JSON string
    json_data = catalog.model_dump_json()

    # Compress and write to disk
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(json_data)


def load_compressed_ir(file_path: Union[str, Path]) -> ProjectCatalog:
    """Reads a Gzip-compressed file, decompresses it, and parses it into a typed ProjectCatalog.

    Args:
        file_path: The file path to load from.

    Returns:
        The deserialized and validated ProjectCatalog instance.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Compressed IR file not found: {path}")

    with gzip.open(path, "rt", encoding="utf-8") as f:
        json_data = f.read()

    return ProjectCatalog.model_validate_json(json_data)


def calculate_sha256(content: Union[str, bytes]) -> str:
    """Calculates the SHA-256 hash of a string or bytes content."""
    if isinstance(content, str):
        content_bytes = content.encode("utf-8")
    else:
        content_bytes = content
    return hashlib.sha256(content_bytes).hexdigest()


def get_file_metadata(file_path: Union[str, Path]) -> tuple[float, int, str]:
    """Retrieves modification time, size, and SHA-256 content hash of a file."""
    path = Path(file_path)
    stat = path.stat()
    mtime = stat.st_mtime
    size = stat.st_size
    with open(path, "rb") as f:
        sha256 = calculate_sha256(f.read())
    return mtime, size, sha256


class L1CacheEntry(BaseModel):
    """Level 1 cache entry representing serialized IR parsing output of an XML source file."""

    mtime: float
    size: int
    sha256: str
    catalog: ProjectCatalog


class L2CacheEntry(BaseModel):
    """Level 2 cache entry representing render signature of an output target file."""

    signature_hash: str


class BuildCache(BaseModel):
    """Pydantic model representing the persistent caching database structure."""

    l1: Dict[str, L1CacheEntry] = Field(default_factory=dict)
    l2: Dict[str, L2CacheEntry] = Field(default_factory=dict)


class BuildCacheManager:
    """Two-Level Incremental Build Cache Manager.

    L1 Parsing Cache: skips processing unchanged XML source files by validating file metadata
    (size/mtime) and content checksum.

    L2 Rendering Cache: skips writing identical generated markdown/HTML targets to disk to avoid
    triggering SSG livereload cascades.
    """

    def __init__(self, product_dir: Union[str, Path]) -> None:
        self.product_dir = Path(product_dir)
        self.cache_path = self.product_dir / ".build_cache.json.gz"
        self._cache = self._load_cache()

    def _load_cache(self) -> BuildCache:
        """Loads and decompresses the persistent cache database from disk."""
        if not self.cache_path.exists():
            return BuildCache()
        try:
            with gzip.open(self.cache_path, "rt", encoding="utf-8") as f:
                json_data = f.read()
            return BuildCache.model_validate_json(json_data)
        except Exception:
            return BuildCache()

    def save(self) -> None:
        """Saves and compresses the current cache database state to disk."""
        self.product_dir.mkdir(parents=True, exist_ok=True)
        json_data = self._cache.model_dump_json()
        with gzip.open(self.cache_path, "wt", encoding="utf-8") as f:
            f.write(json_data)

    def get_l1_entry(self, xml_path: Union[str, Path]) -> Optional[ProjectCatalog]:
        """Returns cached ProjectCatalog if XML source file is unchanged, else None."""
        path_str = str(Path(xml_path).resolve())
        entry = self._cache.l1.get(path_str)
        if not entry:
            return None
        try:
            mtime, size, sha256 = get_file_metadata(xml_path)
            if entry.mtime == mtime and entry.size == size and entry.sha256 == sha256:
                return entry.catalog
        except Exception:
            pass
        return None

    def set_l1_entry(self, xml_path: Union[str, Path], catalog: ProjectCatalog) -> None:
        """Saves ProjectCatalog metadata into the Level 1 parsing cache database."""
        path_str = str(Path(xml_path).resolve())
        try:
            mtime, size, sha256 = get_file_metadata(xml_path)
            self._cache.l1[path_str] = L1CacheEntry(
                mtime=mtime, size=size, sha256=sha256, catalog=catalog
            )
        except Exception:
            pass

    def check_l2_hit(
        self,
        target_path: Union[str, Path],
        entity_signature: str,
        template_content: str,
    ) -> bool:
        """Returns True if Level 2 cache hits and target output file physically exists on disk."""
        path = Path(target_path)
        if not path.exists():
            return False
        path_str = str(path.resolve())
        entry = self._cache.l2.get(path_str)
        if not entry:
            return False
        combined_hash = calculate_sha256(
            entity_signature + calculate_sha256(template_content)
        )
        return entry.signature_hash == combined_hash

    def set_l2_entry(
        self,
        target_path: Union[str, Path],
        entity_signature: str,
        template_content: str,
    ) -> None:
        """Records rendering target signatures inside Level 2 rendering cache database."""
        path_str = str(Path(target_path).resolve())
        combined_hash = calculate_sha256(
            entity_signature + calculate_sha256(template_content)
        )
        self._cache.l2[path_str] = L2CacheEntry(signature_hash=combined_hash)

    def write_if_changed(
        self,
        target_path: Union[str, Path],
        content: str,
        entity_signature: str,
        template_content: str,
    ) -> bool:
        """Writes content to disk only if Level 2 rendering signatures differ, preventing redundant I/O.

        Returns:
            True if write was executed, False if skipped.
        """
        path = Path(target_path)
        if self.check_l2_hit(path, entity_signature, template_content):
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self.set_l2_entry(path, entity_signature, template_content)
        return True
