using Bds.Domain.Identity.Entities;
using Bds.Infrastructure.Identity.Contexts;
using Bds.Infrastructure.Identity.Interfaces;
using Microsoft.EntityFrameworkCore;

namespace Bds.Infrastructure.Identity.Repositories;

public sealed class UserRepository(IdentityContext context) : IUserRepository
{
    public Task<bool> ExistsByEmailAsync(string email, CancellationToken cancellationToken) =>
        context.Users.AnyAsync(u => u.Email == email, cancellationToken);

    public Task<User?> GetByEmailAsync(string email, CancellationToken cancellationToken) =>
        WithRole().FirstOrDefaultAsync(u => u.Email == email, cancellationToken);

    public Task<User?> GetByIdAsync(Guid id, CancellationToken cancellationToken) =>
        WithRole().FirstOrDefaultAsync(u => u.Id == id, cancellationToken);

    public void Add(User user) => context.Users.Add(user);

    private IQueryable<User> WithRole() =>
        context.Users
            .Include(u => u.Role)
            .ThenInclude(r => r.RolePermissions)
            .ThenInclude(rp => rp.Permission);
}