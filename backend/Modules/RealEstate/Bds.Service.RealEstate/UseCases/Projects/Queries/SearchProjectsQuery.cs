using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Projects.Queries;

public sealed record SearchProjectsQuery(
    string? Keyword,
    Guid? ProvinceId,
    Guid? DistrictId,
    string? Status,
    string? SortBy,
    bool Descending,
    int Page,
    int PageSize) : IRequest<PagedResult<ProjectResponse>>;
