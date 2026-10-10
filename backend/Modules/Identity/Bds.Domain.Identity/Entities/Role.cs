using Bds.BuildingBlocks.Domain.Entities;

namespace Bds.Domain.Identity.Entities;
public sealed class Role : BaseEntity
{
    private readonly List<RolePermission> _rolePermissions = [];
    private Role(){}
    public string Name { get; private set; } = null!;
    public string? Description { get; private set; }
    public IReadOnlyCollection<RolePermission> RolePermissions => _rolePermissions;

    public static Role Create(string name, string? description)
    {
        return new Role
        {
            Name = name,
            Description = description,
            CreatedAt = DateTime.UtcNow,
        };
    }

    public void GrantPermission(Permission permission)
    {
        if (_rolePermissions.Any(rp => rp.PermissionId == permission.Id))
        {
            return;
        }
        _rolePermissions.Add(new RolePermission(Id, permission.Id));
        UpdatedAt = DateTime.UtcNow;
    }
}
