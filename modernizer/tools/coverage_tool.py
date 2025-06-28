import xml.etree.ElementTree as ET
import re
import os
from .base_tool import BaseTool

class CoverageTool(BaseTool):
    name = 'coverage'
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        
    def execute(self, args):
        if not args:
            return {'success': False, 'output': 'No project specified'}
        
        parts = args.split()
        project = parts[0]
        specific_files = parts[1:] if len(parts) > 1 else None
        
        result = self.runcommand('dotnet', ['test', project, '--collect:"XPlat Code Coverage"'])
        
        if result['success']:
            formatted_output = self._format_coverage_output(result['output'], specific_files)
            result['output'] = formatted_output
            
        return result
    
    def _format_coverage_output(self, raw_output, specific_files=None):
        coverage_file_match = re.search(r'[^\s]*coverage\.cobertura\.xml', raw_output)
        if not coverage_file_match:
            return raw_output + "\n\nNo coverage file found in output."
        
        coverage_file_path = coverage_file_match.group(0)
        
        try:
            xml_content = self._read_coverage_file(coverage_file_path)
            coverage_data = self._parse_coverage_xml(xml_content)
            
            if specific_files:
                coverage_data = self._filter_coverage_data(coverage_data, specific_files)
            
            formatted_coverage = self._format_coverage_data(coverage_data)
            return formatted_coverage
        except Exception as e:
            return f"Error parsing coverage: {str(e)}"
    
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
                    
                    lines_container = class_elem.find('lines')
                    if lines_container is not None:
                        for line in lines_container.findall('line'):
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
    
    def _filter_coverage_data(self, coverage_data, specific_files):
        """Filter coverage data to only include specified files"""
        filtered_data = {}
        
        for filename, file_data in coverage_data.items():
            for requested_file in specific_files:
                if filename.endswith(requested_file) or requested_file in filename:
                    filtered_data[filename] = file_data
                    break
        
        return filtered_data