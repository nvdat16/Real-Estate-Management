using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Queries.Handlers;

public sealed class SearchPublicListingsHandler(IListingService listingService)
    : IRequestHandler<SearchPublicListingsQuery, PagedResult<ListingResponse>>
{
    public Task<PagedResult<ListingResponse>> Handle(SearchPublicListingsQuery request, CancellationToken cancellationToken) =>
        listingService.SearchPublicAsync(request, cancellationToken);
}
