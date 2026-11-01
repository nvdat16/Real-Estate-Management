using Bds.BuildingBlocks.Application.Abstractions;
using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Queries;

public sealed record SearchMyListingsQuery(Guid UserId, string? Keyword, string? Status, string? Type, PageOptions Paging)
    : IRequest<PagedResult<ListingResponse>>, IPagedQuery;
