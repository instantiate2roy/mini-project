import json
from abc import ABC, abstractmethod
from pathlib import Path

from .tax_result import TaxResult
from .tax_context import TaxContext

class Tax(ABC):

    code: str
    tax_config_file = tax_config_file = Path(__file__).resolve().parent.parent / "configs" / "tax.json"
    tax_configurations={}

    def __init__(self, country_code: str = "UG"):
        """Load json config"""
        if not self.tax_config_file.exists():
            raise FileNotFoundError(f"Tax config not found: {self.tax_config_file}")
 
        data = json.loads(self.tax_config_file.read_text(encoding="utf-8"))
        if country_code not in data["countries"]:
            raise ValueError(f"Country '{country_code}' not found in {self.tax_config_file.name}")
        self.tax_configurations = data["countries"][country_code]
            
    @abstractmethod
    def calculate(self, ctx: TaxContext) -> TaxResult:
        pass