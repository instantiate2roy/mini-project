import json
from abc import ABC, abstractmethod
from pathlib import Path

from .tax_result import TaxResult
from .tax_context import TaxContext

class Tax():

    code: str
    tax_config_file = tax_config_file = Path(__file__).resolve().parent.parent / "configs" / "tax.json"
    tax_configurations={}

    def __init__(self, country_code: str = "UG"):
        """Load json config"""
        if Path(self.tax_config_file).exists():
            data = json.loads(self.tax_config_file.read_text(encoding="utf-8"))
            self.tax_configurations = data["countries"][country_code]
            
    @abstractmethod
    def calculate(self, ctx: TaxContext) -> TaxResult:
        pass