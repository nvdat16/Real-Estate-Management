namespace Bds.Model.Dto.Identity.Requests;

public sealed record LoginRequest(
    string Email,
    string Password
);