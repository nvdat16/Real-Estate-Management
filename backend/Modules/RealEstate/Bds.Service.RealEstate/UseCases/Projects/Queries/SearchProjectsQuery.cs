using Bds.BuildingBlocks.Application.Abstractions;
using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Projects.Queries;

public sealed record SearchProjectsQuery(
    string? Keyword,
    Guid? ProvinceId,
    Guid? DistrictId,
    string? Status,
    PageOptions Paging) : IRequest<PagedResult<ProjectResponse>>, IPagedQuery;
