using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Projects.Queries;

public sealed record GetProjectByIdQuery(Guid Id) : IRequest<ProjectResponse>;
