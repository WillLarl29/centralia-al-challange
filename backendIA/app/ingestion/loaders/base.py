from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RawDocument:
    """Una unidad de texto extraída de un archivo fuente, antes de trocear (chunk)."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseLoader(ABC):
    """Interfaz que debe implementar cada loader de formato (PDF, DOCX, XLSX, etc.)."""

    @abstractmethod
    def load(self, path: Path) -> list[RawDocument]:
        """Carga un archivo y devuelve una lista de RawDocument (uno por página/hoja/slide/registro)."""
        raise NotImplementedError
