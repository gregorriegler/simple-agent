import xml.etree.ElementTree as ET
import re
import os
from .base_tool import BaseTool

class CoverageTool(BaseTool):
    name = 'coverage'
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        
    def execute(self, path):
        result = self.runcommand('dotnet', ['test', path, '--collect:"XPlat Code Coverage"'])
        
        if result['success']:
            # Parse and format coverage data
            formatted_output = self._format_coverage_output(result['output'])
            result['output'] = formatted_output
            
        return result
    
    def _format_coverage_output(self, raw_output):
        # Extract coverage file path from output
        coverage_file_match = re.search(r'TestResults/[^/]+/coverage\.cobertura\.xml', raw_output)
        if not coverage_file_match:
            return raw_output + "\n\nNo coverage file found."
        
        coverage_file_path = coverage_file_match.group(0)
        
        try:
            # Read and parse coverage XML
            xml_content = self._read_coverage_file(coverage_file_path)
            coverage_data = self._parse_coverage_xml(xml_content)
            
            # Format the output
            formatted = raw_output + "\n\n" + self._format_coverage_data(coverage_data)
            return formatted
        except Exception as e:
            return raw_output + f"\n\nError parsing coverage: {str(e)}"
    
    def _read_coverage_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _parse_coverage_xml(self, xml_content):
        root = ET.fromstring(xml_content)
        coverage_data = {}
        
        for package in root.findall('.//package'):
            for class_elem in package.findall('.//class'):
                filename = class_elem.get('filename')
                if filename:
                    class_name = class_elem.get('name')
                    lines_data = []
                    
                    for line in class_elem.findall('.//line'):
                        line_number = int(line.get('number'))
                        hits = int(line.get('hits'))
                        lines_data.append({
                            'number': line_number,
                            'covered': hits > 0
                        })
                    
                    coverage_data[filename] = {
                        'class_name': class_name,
                        'lines': lines_data
                    }
        
        return coverage_data
    
    def _format_coverage_data(self, coverage_data):
        if not coverage_data:
            return "No coverage data found."
        
        output_lines = []
        
        for filename, file_data in coverage_data.items():
            uncovered_lines = [line['number'] for line in file_data['lines'] if not line['covered']]
            
            if uncovered_lines:
                output_lines.append(f"{filename}:")
                for line_num in uncovered_lines:
                    output_lines.append(f"  Line {line_num}: Not covered")
        
        return "\n".join(output_lines) if output_lines else "All lines are covered!"