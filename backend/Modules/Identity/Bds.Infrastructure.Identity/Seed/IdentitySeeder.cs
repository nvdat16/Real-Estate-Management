using Bds.Domain.Identity.Constants;
using Bds.Domain.Identity.Entities;
using Bds.Infrastructure.Identity.Contexts;
using Microsoft.EntityFrameworkCore;

namespace Bds.Infrastructure.Identity.Seed;

public static class IdentitySeeder
{
    private static readonly (string Name, string Description)[] Roles =
    [
        (RoleNames.Admin, "Quản trị hệ thống"),
        (RoleNames.Agent, "Môi giới"),
        (RoleNames.Customer, "Khách hàng"),
    ];

    // Safe to run on every deployment: only inserts roles that do not exist yet.
    public static async Task SeedAsync(IdentityContext context, CancellationToken cancellationToken = default)
    {
        var existingNames = await context.Roles.Select(r => r.Name).ToListAsync(cancellationToken);

        foreach (var (name, description) in Roles.Where(r => !existingNames.Contains(r.Name)))
        {
            context.Roles.Add(Role.Create(name, description));
        }

        await context.SaveChangesAsync(cancellationToken);
    }
}