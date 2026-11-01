using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Queries.Handlers;

public sealed class SearchListingsHandler(IListingService listingService)
    : IRequestHandler<SearchListingsQuery, PagedResult<ListingResponse>>
{
    public Task<PagedResult<ListingResponse>> Handle(SearchListingsQuery request, CancellationToken cancellationToken) =>
        listingService.SearchAsync(request, cancellationToken);
}
