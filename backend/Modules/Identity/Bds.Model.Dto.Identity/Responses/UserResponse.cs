namespace Bds.Model.Dto.Identity.Responses;

public sealed record UserResponse(
    Guid Id,
    string Email,
    string FullName,
    string? PhoneNumber,
    string Role,
    IReadOnlyList<string> Permissions
);