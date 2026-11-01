using Bds.Domain.RealEstate.Enums;
using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Infrastructure.RealEstate.Results;
using Dapper;

namespace Bds.Infrastructure.RealEstate.Repositories;

public sealed class ListingRepository(IRealEstateConnectionFactory connectionFactory) : IListingRepository
{
    public async Task<ListingReadModel?> GetByIdAsync(Guid id, CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        return await connection.QuerySingleOrDefaultAsync<ListingReadModel>(new CommandDefinition(
            "SELECT * FROM realestate.fn_listing_get_by_id(@Id)",
            new { Id = id },
            cancellationToken: cancellationToken));
    }

    public async Task<(IReadOnlyList<ListingReadModel> Items, int TotalCount)> SearchAsync(
        ListingFilter filter,
        CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        var rows = (await connection.QueryAsync<ListingSearchRow>(new CommandDefinition(
            """
            SELECT * FROM realestate.fn_listing_search(
                @PublicOnly, @AgentUserId, @Status, @Keyword, @Type, @MinPrice, @MaxPrice,
                @ProvinceId, @DistrictId, @ProjectId, @MinArea, @MaxArea, @Bedrooms,
                @SortBy, @Descending, @Limit, @Offset)
            """,
            new
            {
                filter.PublicOnly,
                filter.AgentUserId,
                Status = filter.Status?.ToString(),
                Keyword = string.IsNullOrWhiteSpace(filter.Keyword) ? null : filter.Keyword.Trim(),
                Type = filter.Type?.ToString(),
                filter.MinPrice,
                filter.MaxPrice,
                filter.ProvinceId,
                filter.DistrictId,
                filter.ProjectId,
                filter.MinArea,
                filter.MaxArea,
                filter.Bedrooms,
                filter.Paging.SortBy,
                filter.Paging.Descending,
                Limit = filter.Paging.PageSize,
                filter.Paging.Offset,
            },
            cancellationToken: cancellationToken))).AsList();

        var totalCount = rows.Count == 0 ? 0 : (int)rows[0].TotalCount;
        return (rows, totalCount);
    }

    public Task<ListingWriteResult> CreateAsync(
        Guid id,
        Guid userId,
        Guid propertyId,
        ListingType type,
        decimal price,
        string title,
        string description,
        IReadOnlyList<string> imageUrls,
        CancellationToken cancellationToken)
    {
        var parameters = new DynamicParameters(new
        {
            p_id = id,
            p_user_id = userId,
            p_property_id = propertyId,
            p_type = type.ToString(),
            p_price = price,
            p_title = title,
            p_description = description,
            p_image_urls = imageUrls.ToArray(),
        });

        return CallAsync("realestate.sp_listing_create", parameters, cancellationToken);
    }

    public Task<ListingWriteResult> UpdateAsync(
        Guid id,
        Guid userId,
        ListingType type,
        decimal price,
        string title,
        string description,
        IReadOnlyList<string> imageUrls,
        CancellationToken cancellationToken)
    {
        var parameters = new DynamicParameters(new
        {
            p_id = id,
            p_user_id = userId,
            p_type = type.ToString(),
            p_price = price,
            p_title = title,
            p_description = description,
            p_image_urls = imageUrls.ToArray(),
        });

        return CallAsync("realestate.sp_listing_update", parameters, cancellationToken);
    }

    public Task<ListingWriteResult> SubmitAsync(Guid id, Guid userId, CancellationToken cancellationToken) =>
        CallAsync("realestate.sp_listing_submit", new DynamicParameters(new { p_id = id, p_user_id = userId }), cancellationToken);

    public Task<ListingWriteResult> ApproveAsync(Guid id, Guid reviewerId, CancellationToken cancellationToken) =>
        CallAsync("realestate.sp_listing_approve", new DynamicParameters(new { p_id = id, p_reviewer_id = reviewerId }), cancellationToken);

    public Task<ListingWriteResult> RejectAsync(Guid id, Guid reviewerId, string reason, CancellationToken cancellationToken) =>
        CallAsync(
            "realestate.sp_listing_reject",
            new DynamicParameters(new { p_id = id, p_reviewer_id = reviewerId, p_reason = reason }),
            cancellationToken);

    public Task<ListingWriteResult> CloseAsync(Guid id, Guid userId, bool canCloseAny, CancellationToken cancellationToken) =>
        CallAsync(
            "realestate.sp_listing_close",
            new DynamicParameters(new { p_id = id, p_user_id = userId, p_can_close_any = canCloseAny }),
            cancellationToken);

    public Task<ListingWriteResult> DeleteAsync(Guid id, Guid userId, CancellationToken cancellationToken) =>
        CallAsync("realestate.sp_listing_delete", new DynamicParameters(new { p_id = id, p_user_id = userId }), cancellationToken);

    private async Task<ListingWriteResult> CallAsync(string procedure, DynamicParameters parameters, CancellationToken cancellationToken) =>
        (ListingWriteResult)await ProcedureCaller.CallAsync(connectionFactory, procedure, parameters, cancellationToken);

    private sealed class ListingSearchRow : ListingReadModel
    {
        public long TotalCount { get; init; }
    }
}
