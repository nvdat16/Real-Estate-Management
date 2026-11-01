using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands.Handlers;

public sealed class UpdateListingHandler(IListingService listingService) : IRequestHandler<UpdateListingCommand, ListingResponse>
{
    public Task<ListingResponse> Handle(UpdateListingCommand request, CancellationToken cancellationToken) =>
        listingService.UpdateAsync(request, cancellationToken);
}
