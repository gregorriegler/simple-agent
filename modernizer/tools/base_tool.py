import subprocess

class BaseTool:
    name = ''
    
    def __init__(self):
        self.runcommand = None
        
    def execute(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement execute()")
    
    def get_description_from_csharp(self, tool_name):
        try:
            result = subprocess.run(
                ['dotnet', 'run', '--project', 'refactoring-tools/RoslynRefactoring/RoslynRefactoring.csproj', '--', '--describe', tool_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error getting description: {result.stderr}"
        except Exception as e:
            return f"Error getting description: {str(e)}"
    
    def get_arguments_from_csharp(self, tool_name):
        try:
            result = subprocess.run(
                ['dotnet', 'run', '--project', 'refactoring-tools/RoslynRefactoring/RoslynRefactoring.csproj', '--', '--arguments', tool_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error getting arguments: {result.stderr}"
        except Exception as e:
            return f"Error getting arguments: {str(e)}"
    
    def get_info_from_csharp(self, tool_name):
        try:
            result = subprocess.run(
                ['dotnet', 'run', '--project', 'refactoring-tools/RoslynRefactoring/RoslynRefactoring.csproj', '--', '--info', tool_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                import json
                return json.loads(result.stdout.strip())
            else:
                return {"error": f"Error getting info: {result.stderr}"}
        except Exception as e:
            return {"error": f"Error getting info: {str(e)}"}
