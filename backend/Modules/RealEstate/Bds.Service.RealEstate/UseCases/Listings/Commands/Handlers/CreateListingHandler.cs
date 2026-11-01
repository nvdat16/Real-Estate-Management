using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands.Handlers;

public sealed class CreateListingHandler(IListingService listingService) : IRequestHandler<CreateListingCommand, ListingResponse>
{
    public Task<ListingResponse> Handle(CreateListingCommand request, CancellationToken cancellationToken) =>
        listingService.CreateAsync(request, cancellationToken);
}
