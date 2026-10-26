using Bds.Domain.RealEstate.Entities;
using Bds.Domain.RealEstate.Enums;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Infrastructure.RealEstate.Results;

namespace Bds.Infrastructure.RealEstate.Interfaces;

public interface IPropertyRepository
{
    Task<PropertyReadModel?> GetByIdAsync(Guid id, CancellationToken cancellationToken);

    Task<(IReadOnlyList<PropertyReadModel> Items, int TotalCount)> SearchAsync(PropertyFilter filter, CancellationToken cancellationToken);

    Task<PropertyWriteResult> CreateAsync(Property property, CancellationToken cancellationToken);

    Task<PropertyWriteResult> UpdateAsync(
        Guid id,
        decimal area,
        int floor,
        string position,
        int bedrooms,
        Direction direction,
        CancellationToken cancellationToken);

    Task<PropertyWriteResult> DeleteAsync(Guid id, CancellationToken cancellationToken);
}
