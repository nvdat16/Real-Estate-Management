using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Agents.Queries.Handlers;

public sealed class GetMyAgentProfileHandler(IAgentService agentService) : IRequestHandler<GetMyAgentProfileQuery, AgentResponse>
{
    public Task<AgentResponse> Handle(GetMyAgentProfileQuery request, CancellationToken cancellationToken) =>
        agentService.GetMyProfileAsync(request, cancellationToken);
}
