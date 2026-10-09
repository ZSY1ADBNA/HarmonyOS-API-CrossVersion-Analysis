"""Data models for OpenHarmony Official Document RAG system."""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import hashlib


@dataclass
class DocChunk:
    chunk_id: str
    version: str
    kit: str = ""
    subsystem: str = ""
    module: str = ""
    file_path: str = ""
    file_title: str = ""
    heading_level: int = 2
    heading_text: str = ""
    parent_title: str = ""
    heading_path: str = ""
    category: str = "method"  # method, function, interface, class, enum, property, type, overview, error_code
    api_name: str = ""
    full_name: str = ""
    signature: str = ""
    since: str = ""
    deprecated: bool = False
    permission: str = ""
    syscap: str = ""
    atomic_service: str = ""
    description: str = ""
    parameters_summary: str = ""
    return_summary: str = ""
    error_codes_summary: str = ""
    example: str = ""
    raw_content: str = ""
    created_at: str = ""

    @staticmethod
    def generate_id(version: str, file_path: str, heading_path: str, api_name: str, disambiguator: str = "") -> str:
        raw = f"{version}::{file_path}::{heading_path}::{api_name}::{disambiguator}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["deprecated"] = int(self.deprecated)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocChunk":
        import dataclasses
        valid_fields = {f.name for f in dataclasses.fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        if "deprecated" in filtered:
            filtered["deprecated"] = bool(filtered["deprecated"])
        return cls(**filtered)


@dataclass
class SearchFilter:
    version: Optional[str] = None
    kit: Optional[str] = None
    module: Optional[str] = None
    category: Optional[str] = None
    permission: Optional[str] = None
    syscap: Optional[str] = None
    since: Optional[str] = None
    deprecated: Optional[bool] = None


@dataclass
class SearchResult:
    chunk: DocChunk
    score: float
    match_type: str = "keyword"  # exact_name, prefix_name, keyword, condition
    highlights: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "match_type": self.match_type,
            "highlights": self.highlights,
            "chunk": self.chunk.to_dict(),
        }


@dataclass
class VersionComparisonResult:
    api_name: str
    target_versions: List[str]
    found_versions: List[str]
    missing_versions: List[str]
    by_version: Dict[str, List[DocChunk]]
    differences: Dict[str, Any] = field(default_factory=dict)
    summary_markdown: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_name": self.api_name,
            "target_versions": self.target_versions,
            "found_versions": self.found_versions,
            "missing_versions": self.missing_versions,
            "by_version": {v: [c.to_dict() for c in chunks] for v, chunks in self.by_version.items()},
            "differences": self.differences,
            "summary_markdown": self.summary_markdown,
        }
