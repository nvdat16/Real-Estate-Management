namespace Bds.BuildingBlocks.Domain.Entities;

public interface ISoftDelete
{
    bool IsDeleted { get; }

    DateTime? DeletedAt { get; }
}
