# CSharp Style Guide

## All Code
- NO COMMENTS
- whenever brackets or parenthesis surround multiple lines, the closing brackets or the closing parenthesis should be on its own line 
- private fields start with a lower case letter, not with underscores
- NO TryXy patterns 

## Specific to Test Code
- Separate Arrange, Act and Assert by one line of whitespace
- NEVER use Loops or .Where() in a Test. The test knows the expected outcome and references list contents directly or uses prebuilt Collection Asserts.
- Don't do Assert.Multiple. Each Assert stands on its own on its own line.
