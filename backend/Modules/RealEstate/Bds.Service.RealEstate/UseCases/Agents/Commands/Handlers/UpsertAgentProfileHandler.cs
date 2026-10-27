using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Agents.Commands.Handlers;

public sealed class UpsertAgentProfileHandler(IAgentService agentService) : IRequestHandler<UpsertAgentProfileCommand, AgentResponse>
{
    public Task<AgentResponse> Handle(UpsertAgentProfileCommand request, CancellationToken cancellationToken) =>
        agentService.UpsertProfileAsync(request, cancellationToken);
}
