using Bds.Domain.RealEstate.Entities;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Infrastructure.RealEstate.Results;

namespace Bds.Infrastructure.RealEstate.Interfaces;

public interface ICustomerRepository
{
    Task<CustomerReadModel?> GetByIdAsync(Guid id, CancellationToken cancellationToken);

    Task<CustomerReadModel?> GetByUserIdAsync(Guid userId, CancellationToken cancellationToken);

    Task<(IReadOnlyList<CustomerReadModel> Items, int TotalCount)> SearchAsync(ProfileFilter filter, CancellationToken cancellationToken);

    Task<ProfileWriteResult> UpsertAsync(Customer customer, CancellationToken cancellationToken);
}
