using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Properties.Commands.Handlers;

public sealed class CreatePropertyHandler(IPropertyService propertyService) : IRequestHandler<CreatePropertyCommand, PropertyResponse>
{
    public Task<PropertyResponse> Handle(CreatePropertyCommand request, CancellationToken cancellationToken) =>
        propertyService.CreateAsync(request, cancellationToken);
}
