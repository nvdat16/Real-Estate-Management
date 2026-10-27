namespace Bds.Infrastructure.RealEstate.ReadModels;

public class CustomerReadModel
{
    public Guid Id { get; init; }

    public Guid UserId { get; init; }

    public string FullName { get; init; } = null!;

    public string Email { get; init; } = null!;

    public string PhoneNumber { get; init; } = null!;

    public DateOnly? DateOfBirth { get; init; }

    public string? Address { get; init; }

    public DateTime CreatedAt { get; init; }

    public DateTime? UpdatedAt { get; init; }
}
