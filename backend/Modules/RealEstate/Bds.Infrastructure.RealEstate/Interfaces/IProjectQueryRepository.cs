using Bds.Infrastructure.RealEstate.ReadModels;

namespace Bds.Infrastructure.RealEstate.Interfaces;

public interface IProjectQueryRepository
{
    Task<ProjectReadModel?> GetByIdAsync(Guid id, CancellationToken cancellationToken);

    Task<(IReadOnlyList<ProjectReadModel> Items, int TotalCount)> SearchAsync(ProjectFilter filter, CancellationToken cancellationToken);
}
