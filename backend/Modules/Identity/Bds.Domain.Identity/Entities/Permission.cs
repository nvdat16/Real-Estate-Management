using Bds.BuildingBlocks.Domain.Entities;

namespace Bds.Domain.Identity.Entities;
public sealed class Permission : BaseEntity
{
    private Permission(){}

    public string Code { get; set; } = null!;
    public string Name { get; set; } = null!;
    public string Group { get; set; } = null!;

    public static Permission Create(string code, string name, string group)
    {
        return new Permission
        {
            Code = code.Trim(),
            Name = name.Trim(),
            Group = group.Trim(),
            CreatedAt = DateTime.UtcNow,
        };
    }
}