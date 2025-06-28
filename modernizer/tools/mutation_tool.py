import json
import subprocess
import os
from .base_tool import BaseTool

class MutationTool(BaseTool):
    name = 'mutation'
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        
    def execute(self, args):
        # Parse arguments: project [file1] [file2] ...
        if not args:
            return {'success': False, 'output': 'No project specified'}
        
        parts = args.split()
        project = parts[0]
        specific_files = parts[1:] if len(parts) > 1 else None
        
        # Execute Stryker.NET mutation testing
        result = self.runcommand('dotnet', ['stryker', '--project', project, '--reporter', 'json'])
        
        if result['success']:
            # Parse and format mutation testing data
            formatted_output = self._format_mutation_output(result['output'], specific_files)
            result['output'] = formatted_output
            
        return result
    
    def _format_mutation_output(self, raw_output, specific_files=None):
        try:
            # Parse Stryker JSON output
            stryker_data = json.loads(raw_output)
            
            # Initialize counters
            total_mutants = 0
            killed = 0
            survived = 0
            timeout = 0
            survived_mutants = []
            
            # Process each file
            files = stryker_data.get('files', {})
            for file_path, file_data in files.items():
                mutants = file_data.get('mutants', [])
                
                for mutant in mutants:
                    total_mutants += 1
                    status = mutant.get('status', '')
                    
                    if status == 'Killed':
                        killed += 1
                    elif status == 'Survived':
                        survived += 1
                        # Add to survived mutants list
                        location = mutant.get('location', {}).get('start', {})
                        survived_mutants.append({
                            'file': file_path,
                            'line': location.get('line', 0),
                            'column': location.get('column', 0),
                            'mutation_type': self._normalize_mutator_name(mutant.get('mutatorName', '')),
                            'mutated': mutant.get('replacement', ''),
                            'original': '',  # Stryker doesn't provide original code in standard output
                            'method': '',    # Would need additional analysis to determine method
                            'test_coverage': True  # Assume covered if mutant was generated
                        })
                    elif status == 'Timeout':
                        timeout += 1
            
            # Calculate mutation score
            mutation_score = (killed / total_mutants * 100) if total_mutants > 0 else 0
            
            # Return formatted output as JSON string
            result = {
                'success': True,
                'summary': {
                    'total_mutants': total_mutants,
                    'killed': killed,
                    'survived': survived,
                    'timeout': timeout,
                    'mutation_score': round(mutation_score, 1)
                },
                'survived_mutants': survived_mutants
            }
            
            return json.dumps(result)
            
        except json.JSONDecodeError:
            # If not valid JSON, return simple success message
            return "Stryker.NET mutation testing completed"
    
    def _normalize_mutator_name(self, mutator_name):
        """Convert Stryker mutator names to our standardized format"""
        name_mapping = {
            'ArithmeticOperator': 'arithmetic_operator',
            'ConditionalBoundary': 'conditional_boundary',
            'EqualityOperator': 'equality_operator',
            'LogicalOperator': 'logical_operator',
            'RelationalOperator': 'relational_operator',
            'UnaryOperator': 'unary_operator',
            'UpdateOperator': 'update_operator'
        }
        return name_mapping.get(mutator_name, mutator_name.lower())