namespace Bds.Infrastructure.RealEstate.ReadModels;

public sealed class DistrictReadModel
{
    public Guid Id { get; init; }

    public Guid ProvinceId { get; init; }

    public string Code { get; init; } = null!;

    public string Name { get; init; } = null!;
}
