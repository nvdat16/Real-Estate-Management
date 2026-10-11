using Bds.Domain.RealEstate.Entities;

namespace Bds.Infrastructure.RealEstate.Interfaces;

public interface IProjectRepository
{
    Task<Project?> GetByIdAsync(Guid id, CancellationToken cancellationToken);

    Task<bool> ExistsByCodeAsync(string code, CancellationToken cancellationToken);

    void Add(Project project);
}
