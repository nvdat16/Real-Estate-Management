using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Projects.Commands.Handlers;

public sealed class DeleteProjectHandler(IProjectService projectService) : IRequestHandler<DeleteProjectCommand>
{
    public Task Handle(DeleteProjectCommand request, CancellationToken cancellationToken) =>
        projectService.DeleteAsync(request, cancellationToken);
}
