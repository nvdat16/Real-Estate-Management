using Bds.BuildingBlocks.Application.Models;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.UseCases.Properties.Commands;
using Bds.Service.RealEstate.UseCases.Properties.Queries;

namespace Bds.Service.RealEstate.Interfaces;

public interface IPropertyService
{
    Task<PropertyResponse> CreateAsync(CreatePropertyCommand command, CancellationToken cancellationToken);

    Task<PropertyResponse> UpdateAsync(UpdatePropertyCommand command, CancellationToken cancellationToken);

    Task DeleteAsync(DeletePropertyCommand command, CancellationToken cancellationToken);

    Task<PropertyResponse> GetByIdAsync(GetPropertyByIdQuery query, CancellationToken cancellationToken);

    Task<PagedResult<PropertyResponse>> SearchAsync(SearchPropertiesQuery query, CancellationToken cancellationToken);
}
