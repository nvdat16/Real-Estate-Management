using MediatR;

namespace Bds.Service.RealEstate.UseCases.Projects.Commands;

public sealed record DeleteProjectCommand(Guid Id) : IRequest;
