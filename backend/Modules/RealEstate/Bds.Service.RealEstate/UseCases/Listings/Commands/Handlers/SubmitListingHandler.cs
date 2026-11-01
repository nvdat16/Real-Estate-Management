using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands.Handlers;

public sealed class SubmitListingHandler(IListingService listingService) : IRequestHandler<SubmitListingCommand, ListingResponse>
{
    public Task<ListingResponse> Handle(SubmitListingCommand request, CancellationToken cancellationToken) =>
        listingService.SubmitAsync(request, cancellationToken);
}
