using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands.Handlers;

public sealed class CloseListingHandler(IListingService listingService) : IRequestHandler<CloseListingCommand, ListingResponse>
{
    public Task<ListingResponse> Handle(CloseListingCommand request, CancellationToken cancellationToken) =>
        listingService.CloseAsync(request, cancellationToken);
}
