"""
Test Report Generator

Generate test reports for UT test cases including:
- Functionality coverage
- Checkpoints
- Event capture output
- File contents
- Test description
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class TestReportGenerator:
    def __init__(self, test_type: str = 'ut', layer: str = None, service: str = None, report_dir: str = None):
        if report_dir is None:
            project_root = Path(__file__).parent.parent.parent
            if layer and service:
                report_dir = str(project_root / 'tests' / 'report' / test_type / layer / service)
            else:
                report_dir = str(project_root / 'tests' / 'report' / test_type)
        self.report_dir = report_dir
        self.test_type = test_type
        self.layer = layer
        self.service = service
        os.makedirs(self.report_dir, exist_ok=True)

    def generate_report(self, test_name: str, test_class: str, functionality: List[str],
                       checkpoints: List[str], test_data: Dict[str, Any],
                       events_captured: List[Dict] = None,
                       file_contents: Dict[str, str] = None,
                       test_description: str = None,
                       source_file: str = None):
        report = {
            'test_name': test_name,
            'test_class': test_class,
            'test_description': test_description or f"Test case: {test_class}.{test_name}",
            'timestamp': datetime.now().isoformat(),
            'layer': self.layer,
            'service': self.service,
            'functionality_coverage': functionality,
            'checkpoints': checkpoints,
            'test_data': test_data,
            'events_captured': events_captured or [],
            'file_contents': file_contents or {},
            'source_file': source_file or ''
        }

        report_file = os.path.join(self.report_dir, f"{test_name}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

        print(f"[REPORT] Generated: {report_file}")

        return report_file

    def generate_summary_report(self, all_reports: List[Dict]) -> str:
        summary = {
            'generated_at': datetime.now().isoformat(),
            'total_tests': len(all_reports),
            'layer': self.layer,
            'service': self.service,
            'test_reports': all_reports
        }

        summary_file = os.path.join(self.report_dir, 'summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=4, ensure_ascii=False)

        return summary_file
