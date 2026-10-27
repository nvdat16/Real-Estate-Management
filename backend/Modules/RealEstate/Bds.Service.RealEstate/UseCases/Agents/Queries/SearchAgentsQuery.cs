using Bds.BuildingBlocks.Application.Abstractions;
using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Agents.Queries;

public sealed record SearchAgentsQuery(string? Keyword, PageOptions Paging)
    : IRequest<PagedResult<AgentResponse>>, IPagedQuery;
