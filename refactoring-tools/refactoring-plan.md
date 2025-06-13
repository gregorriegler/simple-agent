# 🧹 Refactoring Plan for ExtractCollaboratorInterface

- [x] Add missing `using System;` directive for ArgumentNullException
- [x] Remove hardcoded "PaymentProcessor" string and make it configurable
- [x] Remove unused `UpdateMethodToUseField` method (dead code)
- [x] Extract interface name generation logic to avoid duplication
- [ ] Break down `ProcessDocumentAsync` method into smaller, focused methods
- [ ] Rename `FindCollaboratorTypeFromSelection` to be more descriptive
- [ ] Simplify `FirstCharToLower` method implementation
- [ ] Extract collaborator type detection logic from hardcoded string
- [ ] Improve variable names in `FindUsedMethods` for better readability
- [ ] Consolidate interface name generation in `CollaboratorRewriter` class