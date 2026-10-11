using Bds.Infrastructure.RealEstate.ReadModels;

namespace Bds.Infrastructure.RealEstate.Interfaces;

public interface ILocationQueryRepository
{
    Task<IReadOnlyList<ProvinceReadModel>> GetProvincesAsync(CancellationToken cancellationToken);

    Task<IReadOnlyList<DistrictReadModel>> GetDistrictsAsync(Guid provinceId, CancellationToken cancellationToken);

    Task<bool> DistrictBelongsToProvinceAsync(Guid districtId, Guid provinceId, CancellationToken cancellationToken);
}
