using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Agents.Queries.Handlers;

public sealed class SearchAgentsHandler(IAgentService agentService) : IRequestHandler<SearchAgentsQuery, PagedResult<AgentResponse>>
{
    public Task<PagedResult<AgentResponse>> Handle(SearchAgentsQuery request, CancellationToken cancellationToken) =>
        agentService.SearchAsync(request, cancellationToken);
}
