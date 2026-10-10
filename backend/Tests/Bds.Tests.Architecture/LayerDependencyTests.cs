namespace Bds.Tests.Architecture;

public sealed class LayerDependencyTests
{
    private const string BuildingBlocksPrefix = "Bds.BuildingBlocks.";

    public static TheoryData<string> AllProjects()
    {
        var data = new TheoryData<string>();
        foreach (var project in SolutionProjects.All)
        {
            data.Add(project.Name);
        }

        return data;
    }

    [Fact]
    public void Solution_contains_expected_modules()
    {
        var modules = SolutionProjects.All
            .Select(p => p.Module)
            .OfType<string>()
            .Distinct()
            .Order(StringComparer.Ordinal);

        Assert.Equal(["Identity", "RealEstate", "Storage"], modules);
    }

    [Theory]
    [MemberData(nameof(AllProjects))]
    public void BuildingBlocks_do_not_reference_modules(string name)
    {
        var project = SolutionProjects.Get(name);
        if (!project.Name.StartsWith(BuildingBlocksPrefix, StringComparison.Ordinal))
        {
            return;
        }

        Assert.All(project.References, reference => Assert.StartsWith(BuildingBlocksPrefix, reference));
    }

    [Theory]
    [MemberData(nameof(AllProjects))]
    public void Modules_do_not_reference_other_modules(string name)
    {
        var project = SolutionProjects.Get(name);
        if (project.Module is null)
        {
            return;
        }

        var moduleOfReference = SolutionProjects.All.ToDictionary(p => p.Name, p => p.Module);
        Assert.All(project.References, reference =>
        {
            var target = moduleOfReference[reference];
            Assert.True(
                target is null || target == project.Module,
                $"{project.Name} must not reference {reference} from module {target}.");
        });
    }

    [Theory]
    [MemberData(nameof(AllProjects))]
    public void Module_layers_only_reference_allowed_layers(string name)
    {
        var project = SolutionProjects.Get(name);
        if (project.Module is not { } module)
        {
            return;
        }

        var allowed = AllowedReferences(project.Name, module);
        Assert.All(project.References, reference => Assert.Contains(reference, allowed));
    }

    [Fact]
    public void Host_only_references_presentation_and_building_blocks()
    {
        var host = SolutionProjects.Get("Bds.Host.Api");

        Assert.All(host.References, reference => Assert.True(
            reference.StartsWith("Bds.Presentation.", StringComparison.Ordinal)
                || reference.StartsWith(BuildingBlocksPrefix, StringComparison.Ordinal),
            $"Bds.Host.Api must not reference {reference}."));
    }

    [Fact]
    public void Only_migration_project_applies_migrations()
    {
        var offenders = Directory.EnumerateFiles(SolutionProjects.Root, "*.cs", SearchOption.AllDirectories)
            .Where(path => !path.Contains($"{Path.DirectorySeparatorChar}obj{Path.DirectorySeparatorChar}"))
            .Where(path => !path.Contains($"{Path.DirectorySeparatorChar}Tests{Path.DirectorySeparatorChar}"))
            .Where(path => !path.Contains($"Migrations{Path.DirectorySeparatorChar}Bds.Migration{Path.DirectorySeparatorChar}"))
            .Where(path => File.ReadAllText(path) is var text
                && (text.Contains(".Database.Migrate", StringComparison.Ordinal) || text.Contains("EnsureCreated", StringComparison.Ordinal)))
            .Select(path => Path.GetRelativePath(SolutionProjects.Root, path))
            .ToList();

        Assert.Empty(offenders);
    }

    private static string[] AllowedReferences(string projectName, string module) => projectName switch
    {
        _ when projectName == $"Bds.Domain.{module}" =>
            ["Bds.BuildingBlocks.Domain"],
        _ when projectName == $"Bds.Model.Dto.{module}" =>
            [],
        _ when projectName == $"Bds.Infrastructure.{module}" =>
            [$"Bds.Domain.{module}", "Bds.BuildingBlocks.Domain", "Bds.BuildingBlocks.Application", "Bds.BuildingBlocks.Infrastructure"],
        _ when projectName == $"Bds.Service.{module}" =>
            [$"Bds.Infrastructure.{module}", $"Bds.Domain.{module}", $"Bds.Model.Dto.{module}", "Bds.BuildingBlocks.Domain", "Bds.BuildingBlocks.Application"],
        _ when projectName == $"Bds.Presentation.{module}" =>
            [$"Bds.Service.{module}", $"Bds.Model.Dto.{module}", "Bds.BuildingBlocks.Application"],
        _ => throw new InvalidOperationException($"{projectName} does not follow the Bds.{{Layer}}.{module} naming convention."),
    };
}
