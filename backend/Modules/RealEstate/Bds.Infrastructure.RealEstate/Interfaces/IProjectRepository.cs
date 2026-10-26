using Bds.Domain.RealEstate.Entities;
using Bds.Domain.RealEstate.Enums;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Infrastructure.RealEstate.Results;

namespace Bds.Infrastructure.RealEstate.Interfaces;

public interface IProjectRepository
{
    Task<ProjectReadModel?> GetByIdAsync(Guid id, CancellationToken cancellationToken);

    Task<(IReadOnlyList<ProjectReadModel> Items, int TotalCount)> SearchAsync(ProjectFilter filter, CancellationToken cancellationToken);

    Task<ProjectWriteResult> CreateAsync(Project project, CancellationToken cancellationToken);

    Task<ProjectWriteResult> UpdateAsync(
        Guid id,
        string name,
        Guid provinceId,
        Guid districtId,
        string addressLine,
        string developer,
        ProjectStatus status,
        CancellationToken cancellationToken);

    Task<ProjectWriteResult> DeleteAsync(Guid id, CancellationToken cancellationToken);
}
