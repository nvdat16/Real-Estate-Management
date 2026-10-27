using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Agents.Queries;

public sealed record GetAgentByIdQuery(Guid Id) : IRequest<AgentResponse>;
