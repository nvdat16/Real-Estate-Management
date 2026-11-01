using Bds.Domain.RealEstate.Enums;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Infrastructure.RealEstate.Results;

namespace Bds.Infrastructure.RealEstate.Interfaces;

public interface IListingRepository
{
    Task<ListingReadModel?> GetByIdAsync(Guid id, CancellationToken cancellationToken);

    Task<(IReadOnlyList<ListingReadModel> Items, int TotalCount)> SearchAsync(ListingFilter filter, CancellationToken cancellationToken);

    Task<ListingWriteResult> CreateAsync(
        Guid id,
        Guid userId,
        Guid propertyId,
        ListingType type,
        decimal price,
        string title,
        string description,
        IReadOnlyList<string> imageUrls,
        CancellationToken cancellationToken);

    Task<ListingWriteResult> UpdateAsync(
        Guid id,
        Guid userId,
        ListingType type,
        decimal price,
        string title,
        string description,
        IReadOnlyList<string> imageUrls,
        CancellationToken cancellationToken);

    Task<ListingWriteResult> SubmitAsync(Guid id, Guid userId, CancellationToken cancellationToken);

    Task<ListingWriteResult> ApproveAsync(Guid id, Guid reviewerId, CancellationToken cancellationToken);

    Task<ListingWriteResult> RejectAsync(Guid id, Guid reviewerId, string reason, CancellationToken cancellationToken);

    Task<ListingWriteResult> CloseAsync(Guid id, Guid userId, bool canCloseAny, CancellationToken cancellationToken);

    Task<ListingWriteResult> DeleteAsync(Guid id, Guid userId, CancellationToken cancellationToken);
}
