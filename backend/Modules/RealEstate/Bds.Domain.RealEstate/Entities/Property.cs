using Bds.BuildingBlocks.Domain.Entities;
using Bds.Domain.RealEstate.Enums;

namespace Bds.Domain.RealEstate.Entities;

public sealed class Property : BaseEntity, ISoftDelete
{
    private Property()
    {
    }

    public Guid ProjectId { get; private set; }

    public string Code { get; private set; } = null!;

    public decimal Area { get; private set; }

    public int Floor { get; private set; }

    public string Position { get; private set; } = null!;

    public int Bedrooms { get; private set; }

    public Direction Direction { get; private set; }

    public PropertyStatus Status { get; private set; }

    public bool IsDeleted { get; private set; }

    public DateTime? DeletedAt { get; private set; }

    public static Property Create(Guid projectId, string code, decimal area, int floor, string position, int bedrooms, Direction direction)
    {
        return new Property
        {
            ProjectId = projectId,
            Code = code.Trim().ToUpperInvariant(),
            Area = area,
            Floor = floor,
            Position = position.Trim(),
            Bedrooms = bedrooms,
            Direction = direction,
            Status = PropertyStatus.Available,
            CreatedAt = DateTime.UtcNow,
        };
    }
}
