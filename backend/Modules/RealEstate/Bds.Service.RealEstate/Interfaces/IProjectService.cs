using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.UseCases.Projects.Commands;
using Bds.Service.RealEstate.UseCases.Projects.Queries;

namespace Bds.Service.RealEstate.Interfaces;

public interface IProjectService
{
    Task<ProjectResponse> CreateAsync(CreateProjectCommand command, CancellationToken cancellationToken);

    Task<ProjectResponse> UpdateAsync(UpdateProjectCommand command, CancellationToken cancellationToken);

    Task DeleteAsync(DeleteProjectCommand command, CancellationToken cancellationToken);

    Task<ProjectResponse> GetByIdAsync(GetProjectByIdQuery query, CancellationToken cancellationToken);

    Task<PagedResult<ProjectResponse>> SearchAsync(SearchProjectsQuery query, CancellationToken cancellationToken);
}
