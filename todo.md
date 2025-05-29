- make it respect the rules.md

- commit tool

- organize tools better, it should be easier to add them

- a new tool should be automatically added to the system prompt

- cat and ls dont need checking

-C:\Users\riegl\code\Parrot-Refactoring-Kata\CSharp\Parrot\Parrot.cs(94,20): error CS0103: Der Name "value" ist im aktuellen Kontext nicht vorhanden. [C:\Users\riegl\code\Parrot-Refactoring-Kata\CSharp\Parrot\Parrot.csproj]
API request failed: 429 Client Error: Too Many Requests for url: https://api.anthropic.com/v1/messages

riegl@greglap ~/code/code-modernizer (main)
$

## Claudes /needs 

/need A "Simplify Switch Statement" tool that would convert:
```csharp
private string DetermineCry()
{
    string value;
    switch (_type)
    {
        case ParrotTypeEnum.EUROPEAN:
            value = "Sqoork!";
            break;
        case ParrotTypeEnum.AFRICAN:
            value = "Sqaark!";
            break;
        case ParrotTypeEnum.NORWEGIAN_BLUE:
            value = _voltage > 0 ? "Bzzzzzz" : "...";
            break;
        default:
            throw new ArgumentOutOfRangeException();
    }
    return value;
}
```

to:

```csharp
private string DetermineCry()
{
    switch (_type)
    {
        case ParrotTypeEnum.EUROPEAN:
            return "Sqoork!";
        case ParrotTypeEnum.AFRICAN:
            return "Sqaark!";
        case ParrotTypeEnum.NORWEGIAN_BLUE:
            return _voltage > 0 ? "Bzzzzzz" : "...";
        default:
            throw new ArgumentOutOfRangeException();
    }
}
```

This would remove the temporary variable and directly return the values, making the code more concise and easier to read.



I see there are some issues with the previous refactoring. Let me create a new method for Norwegian Blue speed calculation. First, I'll need a tool that doesn't exist.

/need Add Method - A tool that would add a new method to a class. For example:
/add-method "path/to/project.csproj" "filename.cs" "private double GetNorwegianBlueSpeed() { return _isNailed ? 0 : GetBaseSpeed(_voltage); }"

This would help us fix the current state of the code. The current automatic refactoring has created some issues with duplicate methods and incorrect implementations.

Would you like me to proceed with a different approach or do you have a tool that could help with this situation?



/need Add Constant
I need a tool to add a constant at the class level. For example:
```csharp
private const double LOAD_FACTOR = 9.0;
```
This would help eliminate magic numbers in the code.

Example usage:
/add-constant "path/to/project.csproj" "Parrot.cs" "LOAD_FACTOR" "9.0" "double"