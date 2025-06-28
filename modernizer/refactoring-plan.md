# Refactoring Plan

## Identified Improvements

### mutation_tool.py
- [x] Long method: `_format_mutation_output` is doing too many things (parsing JSON, counting mutants, formatting output)
- [x] Extract method for mutant counting and statistics calculation
- [x] Extract method for survived mutant formatting
- [x] Magic numbers: hardcoded mutation score calculation could be extracted to a constant or method
- [x] Improve variable naming: `stryker_data` could be more descriptive like `mutation_report`

### mutation_tool_test.py
- [ ] Long test method: `test_parse_stryker_output` is testing multiple aspects (parsing, counting, formatting)
- [ ] Extract helper method for creating mock Stryker JSON data
- [ ] Consider splitting into separate tests for different aspects (summary calculation, survived mutants formatting)