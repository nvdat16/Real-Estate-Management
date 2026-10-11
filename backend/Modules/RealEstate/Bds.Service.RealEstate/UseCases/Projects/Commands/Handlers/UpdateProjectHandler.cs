using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Projects.Commands.Handlers;

public sealed class UpdateProjectHandler(IProjectService projectService) : IRequestHandler<UpdateProjectCommand, ProjectResponse>
{
    public Task<ProjectResponse> Handle(UpdateProjectCommand request, CancellationToken cancellationToken) =>
        projectService.UpdateAsync(request, cancellationToken);
}
