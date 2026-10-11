using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.UseCases.Locations.Queries;

namespace Bds.Service.RealEstate.Interfaces;

public interface ILocationService
{
    Task<IReadOnlyList<ProvinceResponse>> GetProvincesAsync(GetProvincesQuery query, CancellationToken cancellationToken);

    Task<IReadOnlyList<DistrictResponse>> GetDistrictsAsync(GetDistrictsQuery query, CancellationToken cancellationToken);
}
