namespace Bds.Model.Dto.Identity.Requests;

public sealed record RegisterRequest(
    string Email,
    string Password,
    string FullName,
    string? PhoneNumber
);