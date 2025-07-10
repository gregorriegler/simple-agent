# Goal: Move Member Up Refactoring Tool

## Objective
Create a new [`MoveMemberUp`](refactoring-tools/RoslynRefactoring/MoveMemberUp.cs) refactoring tool that moves methods from derived classes to their base classes when the methods don't use derived-specific members.

## Current State Analysis
The Code Modernizer currently has several refactoring tools like [`InlineMethod`](refactoring-tools/RoslynRefactoring/InlineMethod.cs:10), [`ExtractMethod`](refactoring-tools/RoslynRefactoring/), [`RenameSymbol`](refactoring-tools/RoslynRefactoring/), but lacks a "Move member up" refactoring capability.

**What We Need to Build:**
- A new C# Roslyn-based refactoring tool
- Integration with the existing [`RefactoringToolDiscovery`](modernizer/tools/refactoring_tool_discovery.py:6) system
- Command-line interface following the existing pattern

## Target Scenarios

### 1. Simple Method Movement (Same File)
```csharp
// Before refactoring
public class Animal
{
    public string Name { get; set; }
}

public class Dog : Animal
{
    public void Speak() => Console.WriteLine("Woof!");
    
    public void DisplayName() => Console.WriteLine($"Name: {Name}"); // Can be moved up
}

// After refactoring - DisplayName moved to Animal class
public class Animal
{
    public string Name { get; set; }
    
    public void DisplayName() => Console.WriteLine($"Name: {Name}");
}

public class Dog : Animal
{
    public void Speak() => Console.WriteLine("Woof!");
}
```

### 2. Method Using Only Base Class Members
```csharp
// Before
public class Vehicle
{
    protected int Speed { get; set; }
    protected string Brand { get; set; }
}

public class Car : Vehicle
{
    private int Doors { get; set; }
    
    public void ShowInfo() => Console.WriteLine($"{Brand} - Speed: {Speed}"); // Can move up
    
    public void ShowDoors() => Console.WriteLine($"Doors: {Doors}"); // Cannot move up
}
```


## Success Criteria
1. **Dependency Analysis**: Correctly identify when a method only uses base class members
2. **Safe Movement**: Move method to base class without breaking compilation
3. **Access Modifier Handling**: Preserve or adjust access modifiers appropriately
4. **Static Method Support**: Handle both instance and static methods
5. **Error Prevention**: Refuse to move methods that use derived-specific members

## Technical Approach
- Use Roslyn semantic analysis to examine method dependencies
- Analyze symbol references within method body
- Check if all referenced members exist in base class
- Perform safe code transformation using Roslyn syntax manipulation
- Follow existing tool patterns in the RoslynRefactoring project

## Implementation Steps
1. Create [`MoveMemberUp.cs`](refactoring-tools/RoslynRefactoring/MoveMemberUp.cs) following existing tool structure
2. Implement dependency analysis to check method safety for movement
3. Add method removal from derived class and insertion into base class
4. Handle access modifier adjustments
5. Create comprehensive test cases
6. Integrate with tool discovery system

## Scenarios (Ordered by Implementation Priority)

### Simple Instance Method - Same File
**Scenario:** Move an instance method that only uses base class members within the same file.
- Method uses only base class properties/fields
- No derived-specific dependencies
- Preserve access modifiers

## TDD Phase: 🔴
