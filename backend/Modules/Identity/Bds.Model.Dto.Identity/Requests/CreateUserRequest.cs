namespace Bds.Model.Dto.Identity.Requests;

public sealed record CreateUserRequest(
    string Email,
    string Password,
    string FullName,
    string? PhoneNumber,
    string Role
);