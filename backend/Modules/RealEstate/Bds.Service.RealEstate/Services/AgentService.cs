using Bds.BuildingBlocks.Application.Exceptions;
using Bds.BuildingBlocks.Application.Models;
using Bds.Domain.RealEstate.Entities;
using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Infrastructure.RealEstate.Results;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using Bds.Service.RealEstate.UseCases.Agents;
using Bds.Service.RealEstate.UseCases.Agents.Commands;
using Bds.Service.RealEstate.UseCases.Agents.Queries;

namespace Bds.Service.RealEstate.Services;

public sealed class AgentService(IAgentRepository agentRepository) : IAgentService
{
    public async Task<AgentResponse> UpsertProfileAsync(UpsertAgentProfileCommand command, CancellationToken cancellationToken)
    {
        var agent = Agent.Create(command.UserId, command.Email, command.FullName, command.PhoneNumber, command.LicenseNumber);

        var result = await agentRepository.UpsertAsync(agent, cancellationToken);
        if (result == ProfileWriteResult.LicenseExists)
        {
            throw AppException.Conflict("Số chứng chỉ hành nghề đã được môi giới khác sử dụng.");
        }

        return await GetMyProfileAsync(new GetMyAgentProfileQuery(command.UserId), cancellationToken);
    }

    public async Task<AgentResponse> GetMyProfileAsync(GetMyAgentProfileQuery query, CancellationToken cancellationToken)
    {
        var agent = await agentRepository.GetByUserIdAsync(query.UserId, cancellationToken)
            ?? throw AppException.NotFound("Bạn chưa có hồ sơ môi giới.");

        return AgentMapping.ToResponse(agent);
    }

    public async Task<AgentResponse> GetByIdAsync(GetAgentByIdQuery query, CancellationToken cancellationToken)
    {
        var agent = await agentRepository.GetByIdAsync(query.Id, cancellationToken)
            ?? throw AppException.NotFound("Không tìm thấy môi giới.");

        return AgentMapping.ToResponse(agent);
    }

    public async Task<PagedResult<AgentResponse>> SearchAsync(SearchAgentsQuery query, CancellationToken cancellationToken)
    {
        var (items, totalCount) = await agentRepository.SearchAsync(new ProfileFilter(query.Keyword, query.Paging), cancellationToken);
        return new PagedResult<AgentResponse>(
            items.Select(AgentMapping.ToResponse).ToList(), query.Paging.Page, query.Paging.PageSize, totalCount);
    }
}
