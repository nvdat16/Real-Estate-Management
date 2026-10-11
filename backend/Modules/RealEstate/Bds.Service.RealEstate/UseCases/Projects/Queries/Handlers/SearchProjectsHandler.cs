using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Projects.Queries.Handlers;

public sealed class SearchProjectsHandler(IProjectService projectService)
    : IRequestHandler<SearchProjectsQuery, PagedResult<ProjectResponse>>
{
    public Task<PagedResult<ProjectResponse>> Handle(SearchProjectsQuery request, CancellationToken cancellationToken) =>
        projectService.SearchAsync(request, cancellationToken);
}
