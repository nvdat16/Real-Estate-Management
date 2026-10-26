using Bds.Domain.RealEstate.Entities;
using Bds.Domain.RealEstate.Enums;
using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Infrastructure.RealEstate.Results;
using Dapper;

namespace Bds.Infrastructure.RealEstate.Repositories;

public sealed class PropertyRepository(IRealEstateConnectionFactory connectionFactory) : IPropertyRepository
{
    public async Task<PropertyReadModel?> GetByIdAsync(Guid id, CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        return await connection.QuerySingleOrDefaultAsync<PropertyReadModel>(new CommandDefinition(
            "SELECT * FROM realestate.fn_property_get_by_id(@Id)",
            new { Id = id },
            cancellationToken: cancellationToken));
    }

    public async Task<(IReadOnlyList<PropertyReadModel> Items, int TotalCount)> SearchAsync(
        PropertyFilter filter,
        CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        var rows = (await connection.QueryAsync<PropertySearchRow>(new CommandDefinition(
            """
            SELECT * FROM realestate.fn_property_search(
                @Keyword, @ProjectId, @Status, @Direction, @MinArea, @MaxArea, @Bedrooms,
                @SortBy, @Descending, @Limit, @Offset)
            """,
            new
            {
                Keyword = string.IsNullOrWhiteSpace(filter.Keyword) ? null : filter.Keyword.Trim(),
                filter.ProjectId,
                Status = filter.Status?.ToString(),
                Direction = filter.Direction?.ToString(),
                filter.MinArea,
                filter.MaxArea,
                filter.Bedrooms,
                filter.SortBy,
                filter.Descending,
                Limit = filter.PageSize,
                Offset = (filter.Page - 1) * filter.PageSize,
            },
            cancellationToken: cancellationToken))).AsList();

        var totalCount = rows.Count == 0 ? 0 : (int)rows[0].TotalCount;
        return (rows, totalCount);
    }

    public Task<PropertyWriteResult> CreateAsync(Property property, CancellationToken cancellationToken)
    {
        var parameters = new DynamicParameters(new
        {
            p_id = property.Id,
            p_project_id = property.ProjectId,
            p_code = property.Code,
            p_area = property.Area,
            p_floor = property.Floor,
            p_position = property.Position,
            p_bedrooms = property.Bedrooms,
            p_direction = property.Direction.ToString(),
        });

        return CallAsync("realestate.sp_property_create", parameters, cancellationToken);
    }

    public Task<PropertyWriteResult> UpdateAsync(
        Guid id,
        decimal area,
        int floor,
        string position,
        int bedrooms,
        Direction direction,
        CancellationToken cancellationToken)
    {
        var parameters = new DynamicParameters(new
        {
            p_id = id,
            p_area = area,
            p_floor = floor,
            p_position = position,
            p_bedrooms = bedrooms,
            p_direction = direction.ToString(),
        });

        return CallAsync("realestate.sp_property_update", parameters, cancellationToken);
    }

    public Task<PropertyWriteResult> DeleteAsync(Guid id, CancellationToken cancellationToken)
    {
        var parameters = new DynamicParameters(new { p_id = id });
        return CallAsync("realestate.sp_property_delete", parameters, cancellationToken);
    }

    private async Task<PropertyWriteResult> CallAsync(string procedure, DynamicParameters parameters, CancellationToken cancellationToken) =>
        (PropertyWriteResult)await ProcedureCaller.CallAsync(connectionFactory, procedure, parameters, cancellationToken);

    private sealed class PropertySearchRow : PropertyReadModel
    {
        public long TotalCount { get; init; }
    }
}
