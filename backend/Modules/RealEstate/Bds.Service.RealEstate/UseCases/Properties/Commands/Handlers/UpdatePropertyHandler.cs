using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Properties.Commands.Handlers;

public sealed class UpdatePropertyHandler(IPropertyService propertyService) : IRequestHandler<UpdatePropertyCommand, PropertyResponse>
{
    public Task<PropertyResponse> Handle(UpdatePropertyCommand request, CancellationToken cancellationToken) =>
        propertyService.UpdateAsync(request, cancellationToken);
}
