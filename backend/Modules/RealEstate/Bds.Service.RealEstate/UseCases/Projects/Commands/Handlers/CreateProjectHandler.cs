using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Projects.Commands.Handlers;

public sealed class CreateProjectHandler(IProjectService projectService) : IRequestHandler<CreateProjectCommand, ProjectResponse>
{
    public Task<ProjectResponse> Handle(CreateProjectCommand request, CancellationToken cancellationToken) =>
        projectService.CreateAsync(request, cancellationToken);
}
