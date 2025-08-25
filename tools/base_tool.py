class BaseTool:
    name = ''
    description = ''
    arguments = []  # List of argument specifications

    def __init__(self):
        self.runcommand = None

    def execute(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement execute()")

    def get_usage_info(self):
        """Generate usage information from argument metadata or return custom info"""
        if hasattr(self, '_custom_usage_info'):
            return self._custom_usage_info()

        return self._generate_usage_info_from_metadata()

    def _generate_usage_info_from_metadata(self):
        """Generate standardized usage info from argument metadata"""
        lines = [f"Tool: {self.name}"]

        if self.description:
            lines.append(f"Description: {self.description}")

        if self.arguments:
            lines.append("")
            lines.append("Arguments:")
            for arg in self.arguments:
                required_str = " (required)" if arg.get('required', False) else " (optional)"
                type_str = f" - {arg['name']}: {arg.get('type', 'string')}{required_str}"
                if 'description' in arg:
                    type_str += f" - {arg['description']}"
                lines.append(type_str)

            # Generate syntax
            lines.append("")
            required_args = [f"<{arg['name']}>" for arg in self.arguments if arg.get('required', False)]
            optional_args = [f"[{arg['name']}]" for arg in self.arguments if not arg.get('required', False)]
            all_args = required_args + optional_args
            syntax = f"/{self.name}"
            if all_args:
                syntax += " " + " ".join(all_args)
            lines.append(f"Usage: {syntax}")

        if hasattr(self, 'examples') and self.examples:
            lines.append("")
            lines.append("Examples:")
            for example in self.examples:
                lines.append(f"  {example}")

        return "\n".join(lines)
