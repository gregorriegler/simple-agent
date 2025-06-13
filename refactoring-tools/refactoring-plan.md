# 🧹 Refactoring Plan for ExtractCollaboratorInterface

- [x] Add missing `using System;` directive for ArgumentNullException
- [x] Remove hardcoded "PaymentProcessor" string and make it configurable
- [x] Remove unused `UpdateMethodToUseField` method (dead code)
- [x] Extract interface name generation logic to avoid duplication
- [x] Break down `ProcessDocumentAsync` method into smaller, focused methods
- [x] Rename `FindCollaboratorTypeFromSelection` to be more descriptive
- [x] Simplify `FirstCharToLower` method implementation
- [x] Extract collaborator type detection logic from hardcoded string
- [x] Improve variable names in `FindUsedMethods` for better readability
- [x] Consolidate interface name generation in `CollaboratorRewriter` class