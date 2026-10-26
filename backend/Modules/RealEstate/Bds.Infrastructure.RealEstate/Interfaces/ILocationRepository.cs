using Bds.Infrastructure.RealEstate.ReadModels;

namespace Bds.Infrastructure.RealEstate.Interfaces;

public interface ILocationRepository
{
    Task<IReadOnlyList<ProvinceReadModel>> GetProvincesAsync(CancellationToken cancellationToken);

    Task<IReadOnlyList<DistrictReadModel>> GetDistrictsAsync(Guid provinceId, CancellationToken cancellationToken);
}
