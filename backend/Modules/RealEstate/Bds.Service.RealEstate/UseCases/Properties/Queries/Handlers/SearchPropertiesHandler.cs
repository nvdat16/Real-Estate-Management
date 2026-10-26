using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Properties.Queries.Handlers;

public sealed class SearchPropertiesHandler(IPropertyService propertyService)
    : IRequestHandler<SearchPropertiesQuery, PagedResult<PropertyResponse>>
{
    public Task<PagedResult<PropertyResponse>> Handle(SearchPropertiesQuery request, CancellationToken cancellationToken) =>
        propertyService.SearchAsync(request, cancellationToken);
}
