using Bds.Domain.RealEstate.Enums;

namespace Bds.Infrastructure.RealEstate.ReadModels;

public class PropertyReadModel
{
    public Guid Id { get; init; }

    public Guid ProjectId { get; init; }

    public string ProjectCode { get; init; } = null!;

    public string ProjectName { get; init; } = null!;

    public string Code { get; init; } = null!;

    public decimal Area { get; init; }

    public int Floor { get; init; }

    public string Position { get; init; } = null!;

    public int Bedrooms { get; init; }

    public Direction Direction { get; init; }

    public PropertyStatus Status { get; init; }

    public DateTime CreatedAt { get; init; }
}
