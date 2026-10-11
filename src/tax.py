import json
from abc import ABC, abstractmethod
from pathlib import Path
from .tax_result import TaxResult
from .tax_context import TaxContext
from .error import TaxConfigError

class Tax(ABC):
    """
    Base tax class, that all my tax type can extend
    """

    code: str = 'TAX' #tax type, overwritted by the child classes
    
    tax_config_file: Path = Path(__file__).resolve().parent.parent / "configs" / "tax.json"
    
    def __init__(self, country_code: str = "UG") -> None:
        """
        Load taxation config from json file
        """
        if not self.tax_config_file.exists(): #Raise exception if no config file
            raise TaxConfigError(f"Tax config not found: {self.tax_config_file}")
 
        data = json.loads(self.tax_config_file.read_text(encoding="utf-8"))
        if country_code not in data["countries"]:
            raise TaxConfigError(f"Country '{country_code}' not found in {self.tax_config_file.name}")
        self.tax_configurations: dict = data["countries"][country_code]
            
    @abstractmethod
    def calculate(self, ctx: TaxContext) -> TaxResult:
        """
        Abstract method to calcule tax, should build and return TaxResult obj 
        """
        pass