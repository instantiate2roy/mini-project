class TaxError(Exception):
    """Base class for every error raised by the tax engine."""
 
 
class InvalidIncomeError(TaxError, ValueError):
    """An income or amount is missing, negative or not a Decimal/Money."""
 
 
class NoScheduleForDateError(TaxError, LookupError):
    """No tax schedule is in force for the requested date."""
 
 
class TaxConfigError(TaxError):
    """configs/tax.json is missing, or lacks a country, tax type or setting."""
 
 
class InvalidContextError(TaxError, ValueError):
    """A TaxContext field other than income is invalid (e.g. month 13, unknown VAT category)."""
 