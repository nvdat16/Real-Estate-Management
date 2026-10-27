using Bds.BuildingBlocks.Domain.Entities;

namespace Bds.Domain.RealEstate.Entities;

public sealed class Agent : BaseEntity
{
    private Agent()
    {
    }

    public Guid UserId { get; private set; }

    public string FullName { get; private set; } = null!;

    public string Email { get; private set; } = null!;

    public string PhoneNumber { get; private set; } = null!;

    public string? LicenseNumber { get; private set; }

    public static Agent Create(Guid userId, string email, string fullName, string phoneNumber, string? licenseNumber)
    {
        return new Agent
        {
            UserId = userId,
            Email = email.Trim().ToLowerInvariant(),
            FullName = fullName.Trim(),
            PhoneNumber = phoneNumber.Trim(),
            LicenseNumber = string.IsNullOrWhiteSpace(licenseNumber) ? null : licenseNumber.Trim().ToUpperInvariant(),
            CreatedAt = DateTime.UtcNow,
        };
    }
}
