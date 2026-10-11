using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Model.Dto.RealEstate.Responses;

namespace Bds.Service.RealEstate.UseCases.Locations;

public static class LocationMapping
{
    public static ProvinceResponse ToResponse(ProvinceReadModel province) => new(province.Id, province.Code, province.Name);

    public static DistrictResponse ToResponse(DistrictReadModel district) => new(district.Id, district.Code, district.Name);
}
