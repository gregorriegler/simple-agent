# Dependency Breaking Mikado Plan

1. For a characterization test entrypoint
1. Identify hard dependencies. Only consider dependencies that harm testability.
1. For each hard dependency generate a strategy to break it
1. Create a list of tiny refactoring steps and 
1. write everything to a markdown file `characterization-test-plan-entrypoint-{entrypoint}.md` 

--- Sample markdown ---

# Entrypoint

```
{
    "FullyQualifiedName": "OrderDispatchKata.UseCase.OrderCreationUseCase.run",
    "FilePath": "C:\\Users\\riegl\\code\\order-dispatch-refactoring-kata\\csharp\\OrderDispatchKata\\UseCase\\OrderCreationUseCase.cs",
    "LineNumber": 21,
    "MethodSignature": "void run(OrderDispatchKata.UseCase.SellItemsRequest request)",
    "ReachableMethodsCount": 22
}
```

# Hard Dependencies

## Dependency X
Details

## Strategy for breaking
... Inject ...

## Tiny Refactoring steps

- [ ] Step 1
- [ ] Step 2
- [ ] Step 3


