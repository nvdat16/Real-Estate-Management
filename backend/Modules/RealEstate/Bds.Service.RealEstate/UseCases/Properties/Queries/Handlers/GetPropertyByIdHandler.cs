using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Properties.Queries.Handlers;

public sealed class GetPropertyByIdHandler(IPropertyService propertyService) : IRequestHandler<GetPropertyByIdQuery, PropertyResponse>
{
    public Task<PropertyResponse> Handle(GetPropertyByIdQuery request, CancellationToken cancellationToken) =>
        propertyService.GetByIdAsync(request, cancellationToken);
}
