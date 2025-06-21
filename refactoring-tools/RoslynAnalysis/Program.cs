using RoslynAnalysis;

var analysisName = args[0];

if (analysisName == "--list-tools")
{
    var allAnalyses = AnalysisInfoGenerator.GetAllAnalysisInfo();
    var json = System.Text.Json.JsonSerializer.Serialize(allAnalyses, new System.Text.Json.JsonSerializerOptions
    {
        WriteIndented = true
    });
    Console.WriteLine(json);
    return;
}

var analysisArgs = args.Skip(3).ToArray();
var analysis = AnalysisInfoGenerator.CreateAnalysis(analysisName, analysisArgs);

var projectPath = args[1].Trim('"');
var fileName = args[2];
var project = new AnalysisProject(projectPath, fileName);

await project.OpenAndApplyAnalysis(analysis);
