using System.Security.Claims;

namespace Bds.BuildingBlocks.Application.Security;

public static class ClaimsPrincipalExtensions
{
    public static Guid GetUserId(this ClaimsPrincipal principal) =>
        Guid.Parse(principal.FindFirst(CustomClaimTypes.UserId)?.Value
            ?? throw new InvalidOperationException("The current principal has no user id claim."));

    public static string GetEmail(this ClaimsPrincipal principal) =>
        principal.FindFirst(CustomClaimTypes.Email)?.Value
            ?? throw new InvalidOperationException("The current principal has no email claim.");
}
