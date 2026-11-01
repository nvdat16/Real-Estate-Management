using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands.Handlers;

public sealed class RejectListingHandler(IListingService listingService) : IRequestHandler<RejectListingCommand, ListingResponse>
{
    public Task<ListingResponse> Handle(RejectListingCommand request, CancellationToken cancellationToken) =>
        listingService.RejectAsync(request, cancellationToken);
}
