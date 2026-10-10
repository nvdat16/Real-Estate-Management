namespace Bds.BuildingBlocks.Domain.Entities;

public abstract class BaseEntity
{
    public Guid Id { get; protected set; } = Guid.CreateVersion7();

    public DateTime CreatedAt { get; set; }

    public DateTime? UpdatedAt { get; set; }
}
