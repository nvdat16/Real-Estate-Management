namespace Bds.Model.Dto.RealEstate.Requests;

public sealed record CreateProjectRequest(
    string Code,
    string Name,
    Guid ProvinceId,
    Guid DistrictId,
    string AddressLine,
    string Developer);
