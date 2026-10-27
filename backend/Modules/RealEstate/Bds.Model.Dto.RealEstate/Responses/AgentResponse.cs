namespace Bds.Model.Dto.RealEstate.Responses;

public sealed record AgentResponse(
    Guid Id,
    Guid UserId,
    string FullName,
    string Email,
    string PhoneNumber,
    string? LicenseNumber,
    DateTime CreatedAt,
    DateTime? UpdatedAt);
