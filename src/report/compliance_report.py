"""
Compliance Report Generator
Generates comprehensive compliance reports for anonymized datasets.

Supports HTML, Markdown, and JSON output formats.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class ComplianceReportGenerator:
    """
    Generates compliance reports documenting anonymization process,
    privacy guarantees, and utility preservation.
    """
    
    def __init__(self):
        """Initialize report generator."""
        self.timestamp = datetime.now()
    
    def generate(self,
                original_data: pd.DataFrame,
                anonymized_data: pd.DataFrame,
                config: Optional[Dict] = None,
                scan_results: Optional[Dict] = None,
                validation_results: Optional[Dict] = None,
                utility_metrics: Optional[Dict] = None,
                output_format: str = "html") -> str:
        """
        Generate compliance report.
        
        Args:
            original_data: Original dataset
            anonymized_data: Anonymized dataset
            config: Configuration used for anonymization
            scan_results: PII detection results
            validation_results: Privacy validation results
            utility_metrics: Utility preservation metrics
            output_format: Output format ('html', 'markdown', or 'json')
        
        Returns:
            Report as string in requested format
        """
        # Gather report data
        report_data = self._gather_report_data(
            original_data,
            anonymized_data,
            config,
            scan_results,
            validation_results,
            utility_metrics
        )
        
        # Generate report in requested format
        if output_format == "html":
            return self._generate_html(report_data)
        elif output_format == "markdown":
            return self._generate_markdown(report_data)
        elif output_format == "json":
            return self._generate_json(report_data)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _gather_report_data(self,
                           original_data: pd.DataFrame,
                           anonymized_data: pd.DataFrame,
                           config: Optional[Dict],
                           scan_results: Optional[Dict],
                           validation_results: Optional[Dict],
                           utility_metrics: Optional[Dict]) -> Dict[str, Any]:
        """Gather all data needed for the report."""
        
        data = {
            'timestamp': self.timestamp.isoformat(),
            'timestamp_formatted': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'dataset_info': {
                'original_records': len(original_data),
                'original_columns': len(original_data.columns),
                'anonymized_records': len(anonymized_data),
                'anonymized_columns': len(anonymized_data.columns),
                'columns': list(original_data.columns)
            },
            'config_name': config.get('metadata', {}).get('name', 'Unknown') if config else 'Custom',
            'config_description': config.get('metadata', {}).get('description', '') if config else '',
            'use_case': config.get('metadata', {}).get('use_case', '') if config else '',
            'scan_results': scan_results or {},
            'validation_results': validation_results or {},
            'utility_metrics': utility_metrics or {},
            'privacy_guarantees': self._extract_privacy_guarantees(validation_results),
            'legal_compliance': self._extract_legal_compliance(config, validation_results)
        }
        
        return data
    
    def _extract_privacy_guarantees(self, validation_results: Optional[Dict]) -> Dict[str, Any]:
        """Extract privacy guarantee information."""
        if not validation_results:
            return {}
        
        guarantees = {
            'overall_status': 'PASSED' if validation_results.get('passed') else 'FAILED',
            'checks': []
        }
        
        for check_name, check_result in validation_results.get('checks', {}).items():
            check_info = {
                'name': check_name.replace('_', ' ').title(),
                'passed': check_result.get('passed', False),
                'message': check_result.get('message', ''),
                'details': {}
            }
            
            # Add check-specific details
            if check_name == 'k_anonymity':
                check_info['details'] = {
                    'Minimum k': check_result.get('min_k', 'N/A'),
                    'Average k': f"{check_result.get('avg_k', 0):.2f}",
                    'Required k': check_result.get('required_k', 'N/A'),
                    'Quasi-identifiers': ', '.join(check_result.get('quasi_identifiers', []))
                }
            elif check_name == 'l_diversity':
                if check_result.get('min_l') is not None:
                    check_info['details'] = {
                        'Minimum l': check_result.get('min_l', 'N/A'),
                        'Average l': f"{check_result.get('avg_l', 0):.2f}",
                        'Required l': check_result.get('required_l', 'N/A'),
                        'Sensitive attributes': ', '.join(check_result.get('sensitive_attributes', []))
                    }
            elif check_name == 'reidentification_risk':
                check_info['details'] = {
                    'High risk records': f"{check_result.get('high_risk_percent', 0):.1f}% ({check_result.get('high_risk_count', 0)} records)",
                    'Medium risk records': f"{check_result.get('medium_risk_percent', 0):.1f}% ({check_result.get('medium_risk_count', 0)} records)",
                    'Low risk records': f"{check_result.get('low_risk_percent', 0):.1f}% ({check_result.get('low_risk_count', 0)} records)",
                    'Maximum acceptable': f"{check_result.get('max_risk_percent', 0)}%"
                }
            
            guarantees['checks'].append(check_info)
        
        return guarantees
    
    def _extract_legal_compliance(self, config: Optional[Dict], 
                                  validation_results: Optional[Dict]) -> Dict[str, Any]:
        """Extract legal compliance information."""
        compliance = {
            'frameworks': [],
            'status': 'COMPLIANT' if validation_results and validation_results.get('passed') else 'NON-COMPLIANT'
        }
        
        if not config:
            return compliance
        
        config_name = config.get('metadata', {}).get('name', '').lower()
        
        # Determine applicable frameworks based on config
        if 'gdpr' in config_name:
            compliance['frameworks'].append({
                'name': 'GDPR (General Data Protection Regulation)',
                'articles': [
                    'Article 25: Data protection by design and by default',
                    'Article 32: Security of processing'
                ],
                'requirements': [
                    'Pseudonymization and anonymization of personal data',
                    'Ability to ensure ongoing confidentiality',
                    'Appropriate technical measures'
                ]
            })
        
        # Add general privacy best practices
        compliance['frameworks'].append({
            'name': 'Privacy Best Practices',
            'principles': [
                'Data minimization',
                'Purpose limitation',
                'Storage limitation',
                'Integrity and confidentiality'
            ]
        })
        
        return compliance
    
    def _generate_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML report."""
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Anonymization Compliance Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }}
        h3 {{
            color: #7f8c8d;
        }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .status-passed {{
            background-color: #d4edda;
            color: #155724;
        }}
        .status-failed {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .info-card {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }}
        .info-card h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .info-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }}
        .check-item {{
            background-color: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            border-left: 4px solid #95a5a6;
        }}
        .check-item.passed {{
            border-left-color: #27ae60;
        }}
        .check-item.failed {{
            border-left-color: #e74c3c;
        }}
        .check-status {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .check-status.passed {{
            color: #27ae60;
        }}
        .check-status.failed {{
            color: #e74c3c;
        }}
        .details-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        .details-table td {{
            padding: 8px;
            border-bottom: 1px solid #ecf0f1;
        }}
        .details-table td:first-child {{
            font-weight: bold;
            width: 40%;
            color: #7f8c8d;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 10px;
            margin: 5px 0;
            background-color: #ecf0f1;
            border-radius: 4px;
        }}
        .metric-name {{
            font-weight: bold;
        }}
        .metric-value {{
            color: #3498db;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .legal-section {{
            background-color: #e8f4f8;
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
        }}
        ul {{
            line-height: 1.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Data Anonymization Compliance Report</h1>
        
        <p><strong>Generated:</strong> {data['timestamp_formatted']}</p>
        <p><strong>Configuration:</strong> {data['config_name']}</p>
        <p><strong>Use Case:</strong> {data['use_case']}</p>
        
        <h2>Executive Summary</h2>
        <div class="status-badge {'status-passed' if data['privacy_guarantees'].get('overall_status') == 'PASSED' else 'status-failed'}">
            Privacy Validation: {data['privacy_guarantees'].get('overall_status', 'UNKNOWN')}
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <h3>Dataset Size</h3>
                <div class="value">{data['dataset_info']['original_records']:,}</div>
                <p>records processed</p>
            </div>
            <div class="info-card">
                <h3>Columns</h3>
                <div class="value">{data['dataset_info']['original_columns']}</div>
                <p>attributes anonymized</p>
            </div>
"""

        # Add PII detection summary if available
        if data['scan_results'] and 'pii_columns' in data['scan_results']:
            pii_count = len(data['scan_results']['pii_columns'])
            html += f"""
            <div class="info-card">
                <h3>PII Detected</h3>
                <div class="value">{pii_count}</div>
                <p>columns containing PII</p>
            </div>
"""
        
        # Add utility metrics if available
        if data['utility_metrics']:
            correlation = data['utility_metrics'].get('correlation_preservation', 0)
            html += f"""
            <div class="info-card">
                <h3>Utility Preserved</h3>
                <div class="value">{correlation:.0%}</div>
                <p>correlation preservation</p>
            </div>
"""
        
        html += """
        </div>
        
        <h2>Privacy Guarantees</h2>
"""
        
        # Add privacy checks
        for check in data['privacy_guarantees'].get('checks', []):
            status_class = 'passed' if check['passed'] else 'failed'
            status_text = '✓ PASSED' if check['passed'] else '✗ FAILED'
            
            html += f"""
        <div class="check-item {status_class}">
            <div class="check-status {status_class}">{status_text}: {check['name']}</div>
            <p>{check['message']}</p>
"""
            
            if check['details']:
                html += """
            <table class="details-table">
"""
                for key, value in check['details'].items():
                    html += f"""
                <tr>
                    <td>{key}</td>
                    <td>{value}</td>
                </tr>
"""
                html += """
            </table>
"""
            
            html += """
        </div>
"""
        
        # Add utility metrics section if available
        if data['utility_metrics']:
            html += """
        <h2>Utility Preservation Metrics</h2>
        <p>These metrics show how much of the original data's utility has been preserved after anonymization.</p>
"""
            
            for metric_name, metric_value in data['utility_metrics'].items():
                if isinstance(metric_value, (int, float)):
                    display_name = metric_name.replace('_', ' ').title()
                    if metric_value <= 1.0:
                        display_value = f"{metric_value:.1%}"
                    else:
                        display_value = f"{metric_value:.2f}"
                    
                    html += f"""
        <div class="metric">
            <span class="metric-name">{display_name}</span>
            <span class="metric-value">{display_value}</span>
        </div>
"""
        
        # Add legal compliance section
        if data['legal_compliance']:
            html += """
        <h2>Legal & Regulatory Compliance</h2>
"""
            
            for framework in data['legal_compliance'].get('frameworks', []):
                html += f"""
        <div class="legal-section">
            <h3>{framework['name']}</h3>
"""
                
                if 'articles' in framework:
                    html += """
            <p><strong>Applicable Articles:</strong></p>
            <ul>
"""
                    for article in framework['articles']:
                        html += f"                <li>{article}</li>\n"
                    html += """
            </ul>
"""
                
                if 'requirements' in framework:
                    html += """
            <p><strong>Requirements Met:</strong></p>
            <ul>
"""
                    for req in framework['requirements']:
                        html += f"                <li>{req}</li>\n"
                    html += """
            </ul>
"""
                
                if 'principles' in framework:
                    html += """
            <p><strong>Principles Applied:</strong></p>
            <ul>
"""
                    for principle in framework['principles']:
                        html += f"                <li>{principle}</li>\n"
                    html += """
            </ul>
"""
                
                html += """
        </div>
"""
        
        # Add PII detection details if available
        if data['scan_results'] and 'pii_columns' in data['scan_results']:
            html += """
        <h2>PII Detection Results</h2>
        <table class="details-table">
            <tr>
                <td style="font-weight: bold;">Column</td>
                <td style="font-weight: bold;">PII Types Detected</td>
            </tr>
"""
            for column, pii_types in data['scan_results']['pii_columns'].items():
                pii_list = ', '.join(pii_types) if isinstance(pii_types, list) else pii_types
                html += f"""
            <tr>
                <td>{column}</td>
                <td>{pii_list}</td>
            </tr>
"""
            html += """
        </table>
"""
        
        # Footer
        html += f"""
        <div class="footer">
            <p>This report was automatically generated by the Data Anonymization Pipeline.</p>
            <p>Report generated: {data['timestamp_formatted']}</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _generate_markdown(self, data: Dict[str, Any]) -> str:
        """Generate Markdown report."""
        
        md = f"""# Data Anonymization Compliance Report

**Generated:** {data['timestamp_formatted']}  
**Configuration:** {data['config_name']}  
**Use Case:** {data['use_case']}

## Executive Summary

**Privacy Validation Status:** {data['privacy_guarantees'].get('overall_status', 'UNKNOWN')}

### Dataset Information

- **Records Processed:** {data['dataset_info']['original_records']:,}
- **Columns:** {data['dataset_info']['original_columns']}
"""
        
        if data['scan_results'] and 'pii_columns' in data['scan_results']:
            pii_count = len(data['scan_results']['pii_columns'])
            md += f"- **PII Columns Detected:** {pii_count}\n"
        
        if data['utility_metrics']:
            correlation = data['utility_metrics'].get('correlation_preservation', 0)
            md += f"- **Utility Preserved:** {correlation:.1%}\n"
        
        md += "\n## Privacy Guarantees\n\n"
        
        for check in data['privacy_guarantees'].get('checks', []):
            status = '✓ PASSED' if check['passed'] else '✗ FAILED'
            md += f"### {status}: {check['name']}\n\n"
            md += f"{check['message']}\n\n"
            
            if check['details']:
                md += "**Details:**\n\n"
                for key, value in check['details'].items():
                    md += f"- **{key}:** {value}\n"
                md += "\n"
        
        if data['utility_metrics']:
            md += "## Utility Preservation Metrics\n\n"
            for metric_name, metric_value in data['utility_metrics'].items():
                if isinstance(metric_value, (int, float)):
                    display_name = metric_name.replace('_', ' ').title()
                    if metric_value <= 1.0:
                        display_value = f"{metric_value:.1%}"
                    else:
                        display_value = f"{metric_value:.2f}"
                    md += f"- **{display_name}:** {display_value}\n"
            md += "\n"
        
        if data['legal_compliance']:
            md += "## Legal & Regulatory Compliance\n\n"
            for framework in data['legal_compliance'].get('frameworks', []):
                md += f"### {framework['name']}\n\n"
                
                if 'articles' in framework:
                    md += "**Applicable Articles:**\n\n"
                    for article in framework['articles']:
                        md += f"- {article}\n"
                    md += "\n"
                
                if 'requirements' in framework:
                    md += "**Requirements Met:**\n\n"
                    for req in framework['requirements']:
                        md += f"- {req}\n"
                    md += "\n"
        
        md += f"\n---\n\n*Report generated: {data['timestamp_formatted']}*\n"
        
        return md
    
    def _generate_json(self, data: Dict[str, Any]) -> str:
        """Generate JSON report."""
        # Convert numpy types to native Python types for JSON serialization
        def convert_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            return obj
        
        data = convert_types(data)
        return json.dumps(data, indent=2)


if __name__ == "__main__":
    # Example usage
    
    # Sample data
    original_df = pd.DataFrame({
        'name': ['John', 'Jane', 'Bob'],
        'age': [25, 30, 35],
        'income': [50000, 60000, 70000]
    })
    
    anonymized_df = pd.DataFrame({
        'name': ['Person_1', 'Person_2', 'Person_3'],
        'age': [25, 30, 35],
        'income': [50000, 60000, 70000]
    })
    
    # Sample results
    validation_results = {
        'passed': True,
        'checks': {
            'k_anonymity': {
                'passed': True,
                'message': 'k-anonymity 5 meets threshold 5',
                'min_k': 5,
                'avg_k': 6.2,
                'required_k': 5,
                'quasi_identifiers': ['age', 'zipcode']
            }
        }
    }
    
    utility_metrics = {
        'correlation_preservation': 0.92,
        'distribution_similarity': 0.88,
        'information_retention': 0.85
    }
    
    # Generate report
    generator = ComplianceReportGenerator()
    report = generator.generate(
        original_data=original_df,
        anonymized_data=anonymized_df,
        validation_results=validation_results,
        utility_metrics=utility_metrics,
        output_format='html'
    )
    
    # Save report
    with open('sample_report.html', 'w') as f:
        f.write(report)
    
    print("Sample report generated: sample_report.html")