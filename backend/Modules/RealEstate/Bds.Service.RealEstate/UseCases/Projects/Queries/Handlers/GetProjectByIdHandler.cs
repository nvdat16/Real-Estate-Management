using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Projects.Queries.Handlers;

public sealed class GetProjectByIdHandler(IProjectService projectService) : IRequestHandler<GetProjectByIdQuery, ProjectResponse>
{
    public Task<ProjectResponse> Handle(GetProjectByIdQuery request, CancellationToken cancellationToken) =>
        projectService.GetByIdAsync(request, cancellationToken);
}
