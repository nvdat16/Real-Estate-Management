using Bds.BuildingBlocks.Domain.Entities;

namespace Bds.Domain.RealEstate.Entities;

public sealed class District : BaseEntity
{
    private District()
    {
    }

    public Guid ProvinceId { get; private set; }

    public string Code { get; private set; } = null!;

    public string Name { get; private set; } = null!;

    public static District Create(Guid provinceId, string code, string name)
    {
        return new District
        {
            ProvinceId = provinceId,
            Code = code.Trim(),
            Name = name.Trim(),
            CreatedAt = DateTime.UtcNow,
        };
    }
}
