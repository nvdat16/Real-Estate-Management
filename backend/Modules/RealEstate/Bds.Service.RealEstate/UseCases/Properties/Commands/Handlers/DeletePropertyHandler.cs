using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Properties.Commands.Handlers;

public sealed class DeletePropertyHandler(IPropertyService propertyService) : IRequestHandler<DeletePropertyCommand>
{
    public Task Handle(DeletePropertyCommand request, CancellationToken cancellationToken) =>
        propertyService.DeleteAsync(request, cancellationToken);
}
