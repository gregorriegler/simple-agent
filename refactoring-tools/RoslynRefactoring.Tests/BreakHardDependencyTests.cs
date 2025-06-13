using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.Formatting;

namespace RoslynRefactoring.Tests;

[TestFixture]
public class BreakHardDependencyTests
{
    [Test]
    public async Task HandleZeroHardDependencies()
    {
        const string code = """
                            public class OrderProcessor
                            {
                                public void Process(Order order)
                                {
                                    order.Status = "Processed";
                                }
                            }
                            """;

        await VerifyBreakHardDependency(code);
    }

    [Test]
    public async Task HandleOneHardDependencyNoConstructor()
    {
        const string code = """
                            public class OrderProcessor
                            {
                                private OrderRepository _orderRepository = OrderRepository.Instance;

                                public void Process(Order order)
                                {
                                    _orderRepository.Save(order);
                                    order.Status = "Processed";
                                }
                            }
                            """;

        await VerifyBreakHardDependency(code);
    }

    [Test]
    public async Task HandleOneHardDependencyWithExistingConstructor()
    {
        const string code = """
                            public class OrderProcessor
                            {
                                private OrderRepository _orderRepository = OrderRepository.Instance;
                                private readonly ProductCatalog _productCatalog;

                                public OrderProcessor(ProductCatalog productCatalog)
                                {
                                    _productCatalog = productCatalog;
                                }

                                public void Process(Order order)
                                {
                                    _orderRepository.Save(order);
                                    _productCatalog.Update(order.ProductId);
                                    order.Status = "Processed";
                                }
                            }
                            """;

        await VerifyBreakHardDependency(code);
    }

    [Test]
    public async Task UpdateCallers()
    {
        const string code = """
                            public class OrderProcessor
                            {
                                private OrderRepository _orderRepository = OrderRepository.Instance;

                                public void Process(Order order)
                                {
                                    _orderRepository.Save(order);
                                    order.Status = "Processed";
                                }
                            }

                            public class OrderService
                            {
                                public void ProcessOrder(Order order)
                                {
                                    var processor = new OrderProcessor();
                                    processor.Process(order);
                                }
                            }
                            """;

        await VerifyBreakHardDependency(code);
    }

    private static async Task VerifyBreakHardDependency(string code)
    {
        var document = CreateDocument(code);
        var breakHardDependency = new BreakHardDependency();
        var updatedDocument = await breakHardDependency.PerformAsync(document);
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