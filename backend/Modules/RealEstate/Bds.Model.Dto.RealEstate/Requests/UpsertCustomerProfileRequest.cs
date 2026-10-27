namespace Bds.Model.Dto.RealEstate.Requests;

public sealed record UpsertCustomerProfileRequest(
    string FullName,
    string PhoneNumber,
    DateOnly? DateOfBirth,
    string? Address);
