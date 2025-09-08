"""Custom reporter for approval tests that uses approve.sh script."""
import os
from approvaltests.reporters import Reporter


class ApproveShReporter(Reporter):
    """Custom reporter that shows approve.sh command instead of move command."""

    def __init__(self):
        pass

    def report(self, received_path, approved_path):
        """Report the difference and show approve.sh command."""
        # Get the test name from the approved file path
        # Extract test name from path like: tests/approved_files/test_name.approved.txt
        approved_filename = os.path.basename(approved_path)
        test_name = approved_filename.replace('.approved.txt', '')

        print(f"\nApproval test failed!")
        print(f"Received: {received_path}")
        print(f"Approved: {approved_path}")

        # Also show the diff if possible
        try:
            with open(received_path, 'r', encoding='utf-8') as f:
                received_content = f.read()
            
            # Try to read approved file, default to empty if it doesn't exist
            try:
                with open(approved_path, 'r', encoding='utf-8') as f:
                    approved_content = f.read()
            except FileNotFoundError:
                approved_content = ""

            print(f"\n--- Expected")
            print(f"+++ Received")
            print(f"@@ Differences @@")

            received_lines = received_content.splitlines()
            approved_lines = approved_content.splitlines()

            max_lines = max(len(received_lines), len(approved_lines))
            for i in range(max_lines):
                approved_line = approved_lines[i] if i < len(approved_lines) else ""
                received_line = received_lines[i] if i < len(received_lines) else ""

                if approved_line != received_line:
                    if approved_line:
                        print(f"- {approved_line}")
                    if received_line:
                        print(f"+ {received_line}")

        except Exception as e:
            print(f"Could not show diff: {e}")
        
        print()
        print()
        print(f"to approve this result: ./approve.sh {test_name}")
        print()

        # Return True to indicate the reporter worked successfully
        return True
