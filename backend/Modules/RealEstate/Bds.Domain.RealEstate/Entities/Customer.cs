using Bds.BuildingBlocks.Domain.Entities;

namespace Bds.Domain.RealEstate.Entities;

public sealed class Customer : BaseEntity
{
    private Customer()
    {
    }

    public Guid UserId { get; private set; }

    public string FullName { get; private set; } = null!;

    public string Email { get; private set; } = null!;

    public string PhoneNumber { get; private set; } = null!;

    public DateOnly? DateOfBirth { get; private set; }

    public string? Address { get; private set; }

    public static Customer Create(Guid userId, string email, string fullName, string phoneNumber, DateOnly? dateOfBirth, string? address)
    {
        return new Customer
        {
            UserId = userId,
            Email = email.Trim().ToLowerInvariant(),
            FullName = fullName.Trim(),
            PhoneNumber = phoneNumber.Trim(),
            DateOfBirth = dateOfBirth,
            Address = string.IsNullOrWhiteSpace(address) ? null : address.Trim(),
            CreatedAt = DateTime.UtcNow,
        };
    }
}
