namespace RoslynRefactoring.Tests;

[TestFixture]
public class RefactoringInfoTests
{
    [Test]
    public async Task GetAllRefactoringInfo_ReturnsAllAvailableRefactorings()
    {
        var result = RefactoringInfoGenerator.GetAllRefactoringInfo();
        await Verify(result);
    }

    [Test]
    public void CreateRefactoring_WithValidName_ReturnsRefactoringInstance()
    {
        var refactoring = RefactoringInfoGenerator.CreateRefactoring("extract-method", ["1:0-2:0", "NewMethod"]);
        
        Assert.That(refactoring, Is.Not.Null);
        Assert.That(refactoring, Is.InstanceOf<IRefactoring>());
    }

    [Test]
    public void CreateRefactoring_WithInvalidName_ThrowsInvalidOperationException()
    {
        var ex = Assert.Throws<InvalidOperationException>(() =>
            RefactoringInfoGenerator.CreateRefactoring("invalid-refactoring", []));
        
        Assert.That(ex.Message, Does.Contain("Unknown refactoring 'invalid-refactoring'"));
        Assert.That(ex.Message, Does.Contain("Available refactorings:"));
    }
}