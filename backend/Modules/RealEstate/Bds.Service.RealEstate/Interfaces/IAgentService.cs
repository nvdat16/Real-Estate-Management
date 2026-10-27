using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.UseCases.Agents.Commands;
using Bds.Service.RealEstate.UseCases.Agents.Queries;

namespace Bds.Service.RealEstate.Interfaces;

public interface IAgentService
{
    Task<AgentResponse> UpsertProfileAsync(UpsertAgentProfileCommand command, CancellationToken cancellationToken);

    Task<AgentResponse> GetMyProfileAsync(GetMyAgentProfileQuery query, CancellationToken cancellationToken);

    Task<AgentResponse> GetByIdAsync(GetAgentByIdQuery query, CancellationToken cancellationToken);

    Task<PagedResult<AgentResponse>> SearchAsync(SearchAgentsQuery query, CancellationToken cancellationToken);
}
