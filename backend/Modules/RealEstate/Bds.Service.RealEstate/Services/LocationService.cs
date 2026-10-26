using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using Bds.Service.RealEstate.UseCases.Locations;
using Bds.Service.RealEstate.UseCases.Locations.Queries;

namespace Bds.Service.RealEstate.Services;

public sealed class LocationService(ILocationRepository locationRepository) : ILocationService
{
    public async Task<IReadOnlyList<ProvinceResponse>> GetProvincesAsync(GetProvincesQuery query, CancellationToken cancellationToken)
    {
        var provinces = await locationRepository.GetProvincesAsync(cancellationToken);
        return provinces.Select(LocationMapping.ToResponse).ToList();
    }

    public async Task<IReadOnlyList<DistrictResponse>> GetDistrictsAsync(GetDistrictsQuery query, CancellationToken cancellationToken)
    {
        var districts = await locationRepository.GetDistrictsAsync(query.ProvinceId, cancellationToken);
        return districts.Select(LocationMapping.ToResponse).ToList();
    }
}
