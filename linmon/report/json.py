"""JSON format report generator."""

import json
from typing import Dict


class JSONReporter:
    """Generates JSON format reports."""
    
    def format(self, report: Dict, indent: int = 2) -> str:
        """
        Format report as JSON.
        
        Args:
            report: Report dictionary from ReportBuilder
            indent: JSON indentation
            
        Returns:
            JSON string
        """
        return json.dumps(report, indent=indent)
