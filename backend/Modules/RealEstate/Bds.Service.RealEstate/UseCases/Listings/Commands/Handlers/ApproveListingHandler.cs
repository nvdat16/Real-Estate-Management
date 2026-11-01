using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands.Handlers;

public sealed class ApproveListingHandler(IListingService listingService) : IRequestHandler<ApproveListingCommand, ListingResponse>
{
    public Task<ListingResponse> Handle(ApproveListingCommand request, CancellationToken cancellationToken) =>
        listingService.ApproveAsync(request, cancellationToken);
}
