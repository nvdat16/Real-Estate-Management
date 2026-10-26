using Bds.BuildingBlocks.Domain.Entities;
using Bds.Domain.RealEstate.Enums;

namespace Bds.Domain.RealEstate.Entities;

public sealed class Project : BaseEntity, ISoftDelete
{
    private Project()
    {
    }

    public string Code { get; private set; } = null!;

    public string Name { get; private set; } = null!;

    public Guid ProvinceId { get; private set; }

    public Guid DistrictId { get; private set; }

    public string AddressLine { get; private set; } = null!;

    public string Developer { get; private set; } = null!;

    public ProjectStatus Status { get; private set; }

    public bool IsDeleted { get; private set; }

    public DateTime? DeletedAt { get; private set; }

    public static Project Create(string code, string name, Guid provinceId, Guid districtId, string addressLine, string developer)
    {
        return new Project
        {
            Code = code.Trim().ToUpperInvariant(),
            Name = name.Trim(),
            ProvinceId = provinceId,
            DistrictId = districtId,
            AddressLine = addressLine.Trim(),
            Developer = developer.Trim(),
            Status = ProjectStatus.Active,
            CreatedAt = DateTime.UtcNow,
        };
    }
}
