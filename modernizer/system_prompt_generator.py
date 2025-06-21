from tools.tool_library import ToolLibrary

class SystemPromptGenerator:
    """Generates system prompts with dynamically discovered tools"""
    
    def __init__(self):
        self.tool_library = ToolLibrary()
    
    def generate_system_prompt(self):
        """Generate the complete system prompt with dynamic tool descriptions"""
        # Read the template system prompt
        template_content = self._read_system_prompt_template()
        
        # Generate the dynamic tools section
        tools_content = self._generate_tools_content()
        
        # Replace the placeholder with dynamic content
        return template_content.replace("{{DYNAMIC_TOOLS_PLACEHOLDER}}", tools_content)
    
    def _read_system_prompt_template(self):
        """Read the system prompt template file"""
        try:
            with open("system-prompt.md", 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError("system-prompt.md template file not found")
    
    def _generate_tools_content(self):
        """Generate the tools content to replace the placeholder"""
        tools_lines = []
        
        for tool in self.tool_library.tools:
            tool_doc = self._generate_tool_documentation(tool)
            if tool_doc:
                tools_lines.append(tool_doc)
        
        return "\n\n".join(tools_lines)
    
    def _generate_tool_documentation(self, tool):
        """Generate documentation for a single tool"""
        if hasattr(tool, 'get_usage_info'):
            # For auto-generated tools with detailed usage info
            usage_info = tool.get_usage_info()
            return self._format_detailed_tool_doc(usage_info)
        else:
            # For simple static tools
            return self._format_simple_tool_doc(tool)
    
    def _format_detailed_tool_doc(self, usage_info):
        """Format detailed tool documentation from usage info"""
        lines = usage_info.split('\n')
        if not lines:
            return ""
        
        # Extract tool name from first line
        tool_line = lines[0]
        if not tool_line.startswith('Tool: '):
            return ""
        
        tool_name = tool_line.replace('Tool: ', '')
        
        # Find description
        description = ""
        for line in lines[1:]:
            if line.startswith('Description: '):
                description = line.replace('Description: ', '')
                break
        
        # Find usage syntax
        usage_syntax = ""
        for line in lines:
            if line.startswith('Usage: '):
                usage_syntax = line.replace('Usage: ', '')
                break
        
        # Format as markdown section
        doc_lines = [f"## {tool_name}"]
        if description:
            doc_lines.append(f"{description}")
        doc_lines.append("Syntax:")
        if usage_syntax:
            doc_lines.append(usage_syntax)
        else:
            doc_lines.append(f"/{tool_name} {{arguments}}")
        
        # Add example if available
        example = self._extract_example_from_usage_info(usage_info)
        if example:
            doc_lines.append("")
            doc_lines.append("e.g.")
            doc_lines.append(example)
        
        return "\n".join(doc_lines)
    
    def _format_simple_tool_doc(self, tool):
        """Format documentation for simple static tools"""
        tool_name = tool.name
        description = getattr(tool, 'description', '')
        
        doc_lines = [f"## {tool_name}"]
        if description:
            doc_lines.append(description)
        
        doc_lines.append("Syntax:")
        
        # Generate syntax based on tool name and common patterns
        if tool_name == 'ls':
            doc_lines.append("/ls {path}")
        elif tool_name == 'cat':
            doc_lines.append("/cat {path}")
        elif tool_name == 'test':
            doc_lines.append("/test {directory}")
        elif tool_name == 'revert':
            doc_lines.append("/revert {directory}")
        else:
            doc_lines.append(f"/{tool_name} {{arguments}}")
        
        return "\n".join(doc_lines)
    
    def _extract_example_from_usage_info(self, usage_info):
        """Extract example from usage info if available"""
        # Look for common example patterns in the usage info
        lines = usage_info.split('\n')
        for i, line in enumerate(lines):
            if 'example' in line.lower() or 'e.g.' in line.lower():
                # Return the next non-empty line as example
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():
                        return lines[j].strip()
        return None
    
    
    def get_system_prompt_for_llm(self):
        """Get the system prompt with tools populated for sending to LLM"""
        return self.generate_system_prompt()