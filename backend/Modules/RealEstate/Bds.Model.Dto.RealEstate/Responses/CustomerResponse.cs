namespace Bds.Model.Dto.RealEstate.Responses;

public sealed record CustomerResponse(
    Guid Id,
    Guid UserId,
    string FullName,
    string Email,
    string PhoneNumber,
    DateOnly? DateOfBirth,
    string? Address,
    DateTime CreatedAt,
    DateTime? UpdatedAt);
