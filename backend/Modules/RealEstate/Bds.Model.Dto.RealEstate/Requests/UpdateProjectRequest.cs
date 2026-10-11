namespace Bds.Model.Dto.RealEstate.Requests;

public sealed record UpdateProjectRequest(
    string Name,
    Guid ProvinceId,
    Guid DistrictId,
    string AddressLine,
    string Developer,
    string Status);
