using Bds.BuildingBlocks.Domain.Entities;

namespace Bds.Domain.RealEstate.Entities;

public sealed class Province : BaseEntity
{
    private Province()
    {
    }

    public string Code { get; private set; } = null!;

    public string Name { get; private set; } = null!;

    public static Province Create(string code, string name)
    {
        return new Province
        {
            Code = code.Trim(),
            Name = name.Trim(),
            CreatedAt = DateTime.UtcNow,
        };
    }
}
