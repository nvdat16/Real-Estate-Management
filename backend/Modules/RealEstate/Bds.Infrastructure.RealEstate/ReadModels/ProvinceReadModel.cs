namespace Bds.Infrastructure.RealEstate.ReadModels;

public sealed class ProvinceReadModel
{
    public Guid Id { get; init; }

    public string Code { get; init; } = null!;

    public string Name { get; init; } = null!;
}
