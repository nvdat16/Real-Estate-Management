using Bds.BuildingBlocks.Application.Security;
using Microsoft.AspNetCore.Authorization;
using Microsoft.Extensions.Options;

namespace Bds.Host.Api.Authorization;

// Any policy name that is not registered explicitly is treated as a permission code,
// so controllers can use [Authorize(Policy = Permissions.X)] without registering each policy.
public sealed class PermissionPolicyProvider(IOptions<AuthorizationOptions> options)
    : DefaultAuthorizationPolicyProvider(options)
{
    public override async Task<AuthorizationPolicy?> GetPolicyAsync(string policyName) =>
        await base.GetPolicyAsync(policyName)
        ?? new AuthorizationPolicyBuilder()
            .RequireAuthenticatedUser()
            .RequireClaim(CustomClaimTypes.Permission, policyName)
            .Build();
}