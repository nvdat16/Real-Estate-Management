using Bds.Domain.RealEstate.Enums;

namespace Bds.Infrastructure.RealEstate.ReadModels;

public class ProjectReadModel
{
    public Guid Id { get; init; }

    public string Code { get; init; } = null!;

    public string Name { get; init; } = null!;

    public Guid ProvinceId { get; init; }

    public string ProvinceName { get; init; } = null!;

    public Guid DistrictId { get; init; }

    public string DistrictName { get; init; } = null!;

    public string AddressLine { get; init; } = null!;

    public string Developer { get; init; } = null!;

    public ProjectStatus Status { get; init; }

    public DateTime CreatedAt { get; init; }
}
