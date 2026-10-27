using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Agents.Queries;

public sealed record GetMyAgentProfileQuery(Guid UserId) : IRequest<AgentResponse>;
