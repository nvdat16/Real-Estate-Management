using Bds.Domain.Identity.Entities;
using Bds.Infrastructure.Identity.Contexts;
using Bds.Infrastructure.Identity.Interfaces;
using Microsoft.EntityFrameworkCore;

namespace Bds.Infrastructure.Identity.Repositories;

public sealed class RoleRepository(IdentityContext context) : IRoleRepository
{
    public Task<Role?> GetByNameAsync(string name, CancellationToken cancellationToken) =>
        context.Roles.FirstOrDefaultAsync(r => r.Name == name, cancellationToken);
}