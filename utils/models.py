from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class Document:
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "text": self.text,
            "metadata": self.metadata
        }
