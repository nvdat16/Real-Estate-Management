namespace Bds.Model.Dto.Identity.Responses;

public sealed record AuthResponse(
    string AccessToken,
    DateTime ExpiresAt,
    UserResponse User
);