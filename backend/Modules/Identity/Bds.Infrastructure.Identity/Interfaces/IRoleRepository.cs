using Bds.Domain.Identity.Entities;

namespace Bds.Infrastructure.Identity.Interfaces;

public interface IRoleRepository
{
    Task<Role?> GetByNameAsync(string name, CancellationToken cancellationToken);
}