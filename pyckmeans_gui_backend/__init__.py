import importlib.metadata
from pathlib import Path

__version__ = importlib.metadata.version(Path(__file__).parent.with_suffix('').name)
