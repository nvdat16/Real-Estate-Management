using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Queries.Handlers;

public sealed class SearchMyListingsHandler(IListingService listingService)
    : IRequestHandler<SearchMyListingsQuery, PagedResult<ListingResponse>>
{
    public Task<PagedResult<ListingResponse>> Handle(SearchMyListingsQuery request, CancellationToken cancellationToken) =>
        listingService.SearchMineAsync(request, cancellationToken);
}
