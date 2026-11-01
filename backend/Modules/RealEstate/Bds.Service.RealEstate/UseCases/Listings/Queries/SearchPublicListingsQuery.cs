using Bds.BuildingBlocks.Application.Abstractions;
using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Queries;

public sealed record SearchPublicListingsQuery(
    string? Keyword,
    string? Type,
    decimal? MinPrice,
    decimal? MaxPrice,
    Guid? ProvinceId,
    Guid? DistrictId,
    Guid? ProjectId,
    decimal? MinArea,
    decimal? MaxArea,
    int? Bedrooms,
    PageOptions Paging) : IRequest<PagedResult<ListingResponse>>, IPagedQuery;
