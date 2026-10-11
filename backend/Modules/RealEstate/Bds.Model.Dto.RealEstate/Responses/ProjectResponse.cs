namespace Bds.Model.Dto.RealEstate.Responses;

public sealed record ProjectResponse(
    Guid Id,
    string Code,
    string Name,
    Guid ProvinceId,
    string ProvinceName,
    Guid DistrictId,
    string DistrictName,
    string AddressLine,
    string Developer,
    string Status,
    DateTime CreatedAt);
