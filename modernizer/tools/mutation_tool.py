import json
import os
from .base_tool import BaseTool

class MutationTool(BaseTool):
    name = 'mutation'
    description = "Run mutation testing to assess test suite quality"
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        
    def execute(self, args):
        if not args:
            return {'success': False, 'output': 'No project specified'}
        
        parts = args.split()
        specific_files = parts[1:] if len(parts) > 1 else None
        stryker_args = [
            'stryker',
            '--reporter', 'json',
            '--verbosity', 'Error'
        ]
        cwd = None
        project = parts[0]
        if project.endswith('.csproj'):
            stryker_args += ['--project', os.path.basename(project)]
            cwd = os.path.dirname(project)
        elif '/' in project or '\\' in project:
            cwd = project
        else:
            stryker_args += ['--project', project]
        
        result = self.runcommand('dotnet', stryker_args, cwd=cwd)
        
        if result['success']:
            formatted_output = self._read_stryker_report(project, result['output'], specific_files)
            result['output'] = formatted_output
        else:
            if 'Could not execute because the specified command or file was not found' in result['output']:
                result['output'] = 'Stryker.NET is not installed. Please install it using: dotnet tool install -g dotnet-stryker'
            
        return result
    
    def _read_stryker_report(self, project_path, stdout_output, specific_files=None):
        """Read Stryker JSON report from file system instead of stdout"""
        try:
            if project_path.endswith('.csproj'):
                work_dir = os.path.dirname(project_path)
            elif '/' in project_path or '\\' in project_path:
                work_dir = project_path
            else:
                work_dir = '.'
            
            possible_dirs = [
                os.path.join(work_dir, 'StrykerOutput'),  # Same directory
                os.path.join(os.path.dirname(work_dir), 'StrykerOutput'),  # Parent directory
                os.path.join(work_dir, '..', 'StrykerOutput')  # Explicit parent
            ]
            
            stryker_output_dir = None
            for dir_path in possible_dirs:
                if os.path.exists(dir_path):
                    stryker_output_dir = dir_path
                    break
            
            if not stryker_output_dir:
                return self._format_mutation_output(stdout_output, specific_files)
            
            report_dirs = [d for d in os.listdir(stryker_output_dir)
                          if os.path.isdir(os.path.join(stryker_output_dir, d))]
            if not report_dirs:
                return self._format_mutation_output(stdout_output, specific_files)
            
            latest_dir = sorted(report_dirs)[-1]
            json_report_path = os.path.join(stryker_output_dir, latest_dir, 'reports', 'mutation-report.json')
            
            if os.path.exists(json_report_path):
                with open(json_report_path, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                return self._format_mutation_output(report_content, specific_files)
            else:
                return self._format_mutation_output(stdout_output, specific_files)
                
        except Exception as e:
            return self._format_mutation_output(stdout_output, specific_files)
    
    def _format_mutation_output(self, raw_output, specific_files=None):
        try:
            mutation_report = json.loads(raw_output)
            
            stats, survived_mutants = self._calculate_mutation_statistics(mutation_report)
            
            result = {
                'success': True,
                'summary': stats,
                'survived_mutants': survived_mutants
            }
            
            return json.dumps(result, indent=2)
            
        except json.JSONDecodeError:
            return json.dumps({
                'success': True,
                'summary': {
                    'total_mutants': 0,
                    'killed': 0,
                    'survived': 0,
                    'timeout': 0,
                    'mutation_score': 0.0
                },
                'survived_mutants': []
            }, indent=2)
    
    def _calculate_mutation_statistics(self, mutation_report):
        """Calculate mutation testing statistics and collect survived mutants"""
        total_mutants = 0
        killed = 0
        survived = 0
        timeout = 0
        survived_mutants = []
        
        files = mutation_report.get('files', {})
        for file_path, file_data in files.items():
            mutants = file_data.get('mutants', [])
            
            for mutant in mutants:
                total_mutants += 1
                status = mutant.get('status', '')
                
                if status == 'Killed':
                    killed += 1
                elif status == 'Survived':
                    survived += 1
                    survived_mutants.append(self._format_survived_mutant(mutant, file_path))
                elif status == 'Timeout':
                    timeout += 1
        
        mutation_score = self._calculate_mutation_score(killed, total_mutants)
        
        stats = {
            'total_mutants': total_mutants,
            'killed': killed,
            'survived': survived,
            'timeout': timeout,
            'mutation_score': round(mutation_score, 1)
        }
        
        return stats, survived_mutants
    
    def _format_survived_mutant(self, mutant, file_path):
        """Format a survived mutant into our standard structure"""
        location = mutant.get('location', {}).get('start', {})
        return {
            'file': file_path,
            'line': location.get('line', 0),
            'column': location.get('column', 0),
            'mutation_type': self._normalize_mutator_name(mutant.get('mutatorName', '')),
            'mutated': mutant.get('replacement', ''),
            'original': '',  # Stryker doesn't provide original code in standard output
            'method': '',    # Would need additional analysis to determine method
            'test_coverage': True  # Assume covered if mutant was generated
        }
    
    def _calculate_mutation_score(self, killed, total_mutants):
        """Calculate the mutation score percentage"""
        return (killed / total_mutants * 100) if total_mutants > 0 else 0
    
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