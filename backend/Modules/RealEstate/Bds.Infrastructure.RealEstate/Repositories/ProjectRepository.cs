using Bds.Domain.RealEstate.Entities;
using Bds.Infrastructure.RealEstate.Contexts;
using Bds.Infrastructure.RealEstate.Interfaces;
using Microsoft.EntityFrameworkCore;

namespace Bds.Infrastructure.RealEstate.Repositories;

public sealed class ProjectRepository(RealEstateContext context) : IProjectRepository
{
    public Task<Project?> GetByIdAsync(Guid id, CancellationToken cancellationToken) =>
        context.Projects.FirstOrDefaultAsync(p => p.Id == id, cancellationToken);

    public Task<bool> ExistsByCodeAsync(string code, CancellationToken cancellationToken) =>
        context.Projects.AnyAsync(p => p.Code == code, cancellationToken);

    public void Add(Project project) => context.Projects.Add(project);
}
