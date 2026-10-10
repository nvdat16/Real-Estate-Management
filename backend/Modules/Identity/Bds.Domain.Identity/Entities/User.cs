using System.Runtime.CompilerServices;
using System.Text;
using Bds.BuildingBlocks.Domain.Entities;

namespace Bds.Domain.Identity.Entities;
public sealed class User : BaseEntity
{
    private User(){}

    public string Email { get; private set; } = null!;
    public string PasswordHash { get; private set; } = null!;
    public string FullName { get; private set; } = null!;
    public string? PhoneNumber { get; private set; }
    public Guid RoleId { get; private set; }
    public Role Role { get; private set;} = null!;
    public bool IsLocked { get; private set; }
    public DateTime? LastLoginAt { get; private set; }

    public static User Create(string email, string passwordHash, string fullName, string? phoneNumber, Role role)
    {
        return new User
        {
            Email = NormalizeEmail(email),
            PasswordHash = passwordHash,
            FullName = fullName.Trim(),
            PhoneNumber = phoneNumber?.Trim(),
            RoleId = role.Id,
            Role = role,
            CreatedAt = DateTime.UtcNow,
        };
    }

    public static string NormalizeEmail(string email) => email.Trim().ToLowerInvariant();

    public void ChangeRole(Role role)
    {
        RoleId = role.Id;
        Role = role;
        UpdatedAt = DateTime.UtcNow;
    }

    public void ChangePassword(string passwordHash)
    {
        PasswordHash = passwordHash;
        UpdatedAt = DateTime.UtcNow;
    }

    public void RecordLogin(DateTime now)
    {
        LastLoginAt = now;
    }

    public void Lock()
    {
        IsLocked = true;
        UpdatedAt = DateTime.UtcNow;
    }

    public void Unlock()
    {
        IsLocked = false;
        UpdatedAt = DateTime.UtcNow;
    }
}
