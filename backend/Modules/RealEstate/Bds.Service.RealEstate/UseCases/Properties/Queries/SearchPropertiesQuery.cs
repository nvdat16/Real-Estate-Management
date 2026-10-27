using Bds.BuildingBlocks.Application.Abstractions;
using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Properties.Queries;

public sealed record SearchPropertiesQuery(
    string? Keyword,
    Guid? ProjectId,
    string? Status,
    string? Direction,
    decimal? MinArea,
    decimal? MaxArea,
    int? Bedrooms,
    PageOptions Paging) : IRequest<PagedResult<PropertyResponse>>, IPagedQuery;
