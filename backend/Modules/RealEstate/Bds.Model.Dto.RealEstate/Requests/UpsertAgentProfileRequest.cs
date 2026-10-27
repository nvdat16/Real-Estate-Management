namespace Bds.Model.Dto.RealEstate.Requests;

public sealed record UpsertAgentProfileRequest(
    string FullName,
    string PhoneNumber,
    string? LicenseNumber);
