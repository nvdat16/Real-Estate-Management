using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Agents.Queries.Handlers;

public sealed class GetAgentByIdHandler(IAgentService agentService) : IRequestHandler<GetAgentByIdQuery, AgentResponse>
{
    public Task<AgentResponse> Handle(GetAgentByIdQuery request, CancellationToken cancellationToken) =>
        agentService.GetByIdAsync(request, cancellationToken);
}
