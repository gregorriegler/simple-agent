using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Formatting;

namespace RoslynRefactoring.Tests;

[TestFixture]
public class ExtractCollaboratorInterfaceTests
{
    [Test]
    public async Task HandleZeroCollaborators()
    {
        const string code = """
                            public class OrderService
                            {
                                public void ProcessOrder(Order order)
                                {
                                    order.Status = "Processed";
                                }
                            }
                            """;

        await VerifyExtractCollaboratorInterface(code);
    }

    [Test]
    public async Task HandleOneCollaboratorOneMethod()
    {
        const string code = """
                            public class OrderService
                            {
                                private readonly PaymentProcessor _paymentProcessor;
                                
                                public OrderService(PaymentProcessor paymentProcessor)
                                {
                                    _paymentProcessor = paymentProcessor;
                                }
                                
                                public void ProcessOrder(Order order)
                                {
                                    _paymentProcessor.ProcessPayment();
                                }
                            }
                            """;

        await VerifyExtractCollaboratorInterface(code, "3:29-3:46");
    }

    [Test]
    public async Task HandleOneCollaboratorOneProperty()
    {
        const string code = """
                            public class OrderService
                            {
                                private readonly PaymentProcessor _paymentProcessor;
                                
                                public OrderService(PaymentProcessor paymentProcessor)
                                {
                                    _paymentProcessor = paymentProcessor;
                                }
                                
                                public void ProcessOrder(Order order)
                                {
                                    var status = _paymentProcessor.Status;
                                }
                            }
                            """;

        await VerifyExtractCollaboratorInterface(code, "3:29-3:46");
    }

    [Test]
    public async Task HandleOneCollaboratorMultipleMembers()
    {
        const string code = """
                            public class OrderService
                            {
                                private readonly PaymentProcessor _paymentProcessor;
                                
                                public OrderService(PaymentProcessor paymentProcessor)
                                {
                                    _paymentProcessor = paymentProcessor;
                                }
                                
                                public void ProcessOrder(Order order)
                                {
                                    _paymentProcessor.ProcessPayment();
                                    var status = _paymentProcessor.Status;
                                }
                            }
                            """;

        await VerifyExtractCollaboratorInterface(code, "3:29-3:46");
    }

    [Test]
    public async Task HandleCollaboratorWithExistingInterface()
    {
        const string code = """
                            public interface IPaymentProcessor
                            {
                                void ProcessPayment();
                            }
                            
                            public class PaymentProcessor : IPaymentProcessor
                            {
                                public void ProcessPayment() { }
                            }
                            
                            public class OrderService
                            {
                                private readonly PaymentProcessor _paymentProcessor;
                                
                                public OrderService(PaymentProcessor paymentProcessor)
                                {
                                    _paymentProcessor = paymentProcessor;
                                }
                                
                                public void ProcessOrder(Order order)
                                {
                                    _paymentProcessor.ProcessPayment();
                                }
                            }
                            """;

        await VerifyExtractCollaboratorInterface(code, "15:29-15:46");
    }

    [Test]
    public async Task HandlePropertyInjection()
    {
        const string code = """
                            public class OrderService
                            {
                                public PaymentProcessor PaymentProcessor { get; set; }
                                
                                public void ProcessOrder(Order order)
                                {
                                    PaymentProcessor.ProcessPayment();
                                }
                            }
                            """;

        await VerifyExtractCollaboratorInterface(code, "3:21-3:38");
    }

    private static async Task VerifyExtractCollaboratorInterface(string code, string selectionText = "")
    {
        var document = CreateDocument(code);
        
        var selection = string.IsNullOrEmpty(selectionText)
            ? CodeSelection.Parse("1:0-1:0")
            : CodeSelection.Parse(selectionText);
            
        var extractCollaboratorInterface = new ExtractCollaboratorInterface(selection);
        var updatedDocument = await extractCollaboratorInterface.PerformAsync(document);
        var formatted = Formatter.Format((await updatedDocument.GetSyntaxRootAsync())!, new AdhocWorkspace());
        await Verify(formatted.ToFullString());
    }

    private static Document CreateDocument(string code)
    {
        var workspace = new AdhocWorkspace();
        var project = workspace.CurrentSolution.AddProject("TestProject", "TestProject.dll", LanguageNames.CSharp)
            .AddMetadataReference(MetadataReference.CreateFromFile(typeof(object).Assembly.Location));

        return project.AddDocument("Test.cs", code);
    }
}