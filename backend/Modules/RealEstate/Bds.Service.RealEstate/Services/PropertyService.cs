using Bds.BuildingBlocks.Application.Exceptions;
using Bds.BuildingBlocks.Application.Models;
using Bds.Domain.RealEstate.Entities;
using Bds.Domain.RealEstate.Enums;
using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using Bds.Service.RealEstate.UseCases.Properties;
using Bds.Service.RealEstate.UseCases.Properties.Commands;
using Bds.Service.RealEstate.UseCases.Properties.Queries;

namespace Bds.Service.RealEstate.Services;

public sealed class PropertyService(IPropertyRepository propertyRepository) : IPropertyService
{
    public async Task<PropertyResponse> CreateAsync(CreatePropertyCommand command, CancellationToken cancellationToken)
    {
        var direction = Enum.Parse<Direction>(command.Direction, ignoreCase: true);
        var property = Property.Create(
            command.ProjectId, command.Code, command.Area, command.Floor, command.Position, command.Bedrooms, direction);

        var result = await propertyRepository.CreateAsync(property, cancellationToken);
        PropertyRules.EnsureSuccess(result);

        return await GetByIdAsync(new GetPropertyByIdQuery(property.Id), cancellationToken);
    }

    public async Task<PropertyResponse> UpdateAsync(UpdatePropertyCommand command, CancellationToken cancellationToken)
    {
        var direction = Enum.Parse<Direction>(command.Direction, ignoreCase: true);

        var result = await propertyRepository.UpdateAsync(
            command.Id, command.Area, command.Floor, command.Position.Trim(), command.Bedrooms, direction, cancellationToken);
        PropertyRules.EnsureSuccess(result);

        return await GetByIdAsync(new GetPropertyByIdQuery(command.Id), cancellationToken);
    }

    public async Task DeleteAsync(DeletePropertyCommand command, CancellationToken cancellationToken)
    {
        var result = await propertyRepository.DeleteAsync(command.Id, cancellationToken);
        PropertyRules.EnsureSuccess(result);
    }

    public async Task<PropertyResponse> GetByIdAsync(GetPropertyByIdQuery query, CancellationToken cancellationToken)
    {
        var property = await propertyRepository.GetByIdAsync(query.Id, cancellationToken)
            ?? throw AppException.NotFound(PropertyRules.NotFoundMessage);

        return PropertyMapping.ToResponse(property);
    }

    public async Task<PagedResult<PropertyResponse>> SearchAsync(SearchPropertiesQuery query, CancellationToken cancellationToken)
    {
        var filter = new PropertyFilter(
            query.Keyword,
            query.ProjectId,
            query.Status is null ? null : Enum.Parse<PropertyStatus>(query.Status, ignoreCase: true),
            query.Direction is null ? null : Enum.Parse<Direction>(query.Direction, ignoreCase: true),
            query.MinArea,
            query.MaxArea,
            query.Bedrooms,
            query.Paging);

        var (items, totalCount) = await propertyRepository.SearchAsync(filter, cancellationToken);
        return new PagedResult<PropertyResponse>(
            items.Select(PropertyMapping.ToResponse).ToList(), query.Paging.Page, query.Paging.PageSize, totalCount);
    }
}
