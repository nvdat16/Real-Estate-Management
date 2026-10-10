using System.Xml.Linq;

namespace Bds.Tests.Architecture;

public sealed record ProjectInfo(string Name, string Path, IReadOnlyList<string> References)
{
    public string? Module => ModuleOf(Path);

    public static string? ModuleOf(string path)
    {
        var parts = path.Split(System.IO.Path.DirectorySeparatorChar);
        var index = Array.IndexOf(parts, "Modules");
        return index >= 0 && index + 1 < parts.Length ? parts[index + 1] : null;
    }
}

public static class SolutionProjects
{
    public const string SolutionFileName = "Bds.Website.sln";

    private static readonly Lazy<string> _root = new(FindRoot);
    private static readonly Lazy<IReadOnlyList<ProjectInfo>> _all = new(LoadAll);

    public static string Root => _root.Value;

    public static IReadOnlyList<ProjectInfo> All => _all.Value;

    public static ProjectInfo Get(string name) => All.Single(p => p.Name == name);

    private static string FindRoot()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null && !File.Exists(System.IO.Path.Combine(directory.FullName, SolutionFileName)))
        {
            directory = directory.Parent;
        }

        return directory?.FullName ?? throw new InvalidOperationException($"Cannot locate {SolutionFileName}.");
    }

    private static IReadOnlyList<ProjectInfo> LoadAll()
    {
        return Directory.EnumerateFiles(Root, "*.csproj", SearchOption.AllDirectories)
            .Where(path => !IsBuildOutput(path))
            .Select(Load)
            .OrderBy(p => p.Name, StringComparer.Ordinal)
            .ToList();
    }

    private static ProjectInfo Load(string path)
    {
        var references = XDocument.Load(path)
            .Descendants("ProjectReference")
            .Select(e => (string?)e.Attribute("Include"))
            .OfType<string>()
            .Select(include => System.IO.Path.GetFileNameWithoutExtension(include.Replace('\\', System.IO.Path.DirectorySeparatorChar)))
            .ToList();

        var relative = System.IO.Path.GetRelativePath(Root, path);
        return new ProjectInfo(System.IO.Path.GetFileNameWithoutExtension(path), relative, references);
    }

    private static bool IsBuildOutput(string path)
    {
        var separator = System.IO.Path.DirectorySeparatorChar;
        return path.Contains($"{separator}bin{separator}") || path.Contains($"{separator}obj{separator}");
    }
}
