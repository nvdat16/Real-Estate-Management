using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Queries.Handlers;

public sealed class GetListingByIdHandler(IListingService listingService) : IRequestHandler<GetListingByIdQuery, ListingResponse>
{
    public Task<ListingResponse> Handle(GetListingByIdQuery request, CancellationToken cancellationToken) =>
        listingService.GetByIdAsync(request, cancellationToken);
}
