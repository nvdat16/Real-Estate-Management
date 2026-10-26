using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Model.Dto.RealEstate.Responses;

namespace Bds.Service.RealEstate.UseCases.Properties;

public static class PropertyMapping
{
    public static PropertyResponse ToResponse(PropertyReadModel property) => new(
        property.Id,
        property.ProjectId,
        property.ProjectCode,
        property.ProjectName,
        property.Code,
        property.Area,
        property.Floor,
        property.Position,
        property.Bedrooms,
        property.Direction.ToString(),
        property.Status.ToString(),
        property.CreatedAt);
}
