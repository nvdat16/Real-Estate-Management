using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands.Handlers;

public sealed class DeleteListingHandler(IListingService listingService) : IRequestHandler<DeleteListingCommand>
{
    public Task Handle(DeleteListingCommand request, CancellationToken cancellationToken) =>
        listingService.DeleteAsync(request, cancellationToken);
}
