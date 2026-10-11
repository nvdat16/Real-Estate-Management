using Bds.Infrastructure.RealEstate.Contexts;
using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.ReadModels;
using Dapper;
using Microsoft.EntityFrameworkCore;

namespace Bds.Infrastructure.RealEstate.Repositories;

public sealed class ProjectQueryRepository(RealEstateContext context) : IProjectQueryRepository
{
    private const string SelectColumns = """
        SELECT p.id AS Id, p.code AS Code, p.name AS Name,
               p.province_id AS ProvinceId, pr.name AS ProvinceName,
               p.district_id AS DistrictId, d.name AS DistrictName,
               p.address_line AS AddressLine, p.developer AS Developer,
               p.status AS Status, p.created_at AS CreatedAt
        FROM realestate.projects p
        JOIN realestate.provinces pr ON pr.id = p.province_id
        JOIN realestate.districts d ON d.id = p.district_id
        """;

    // Only these columns can be sorted on; the client value is never concatenated into SQL.
    private static readonly Dictionary<string, string> SortColumns = new(StringComparer.OrdinalIgnoreCase)
    {
        ["code"] = "p.code",
        ["name"] = "p.name",
        ["createdAt"] = "p.created_at",
    };

    public Task<ProjectReadModel?> GetByIdAsync(Guid id, CancellationToken cancellationToken)
    {
        const string sql = SelectColumns + " WHERE p.id = @Id AND p.is_deleted = false";

        var connection = context.Database.GetDbConnection();
        return connection.QuerySingleOrDefaultAsync<ProjectReadModel>(
            new CommandDefinition(sql, new { Id = id }, cancellationToken: cancellationToken));
    }

    public async Task<(IReadOnlyList<ProjectReadModel> Items, int TotalCount)> SearchAsync(
        ProjectFilter filter,
        CancellationToken cancellationToken)
    {
        // Soft-deleted rows must be excluded by hand: EF's query filter does not apply to raw SQL.
        var conditions = new List<string> { "p.is_deleted = false" };
        var parameters = new DynamicParameters();

        if (!string.IsNullOrWhiteSpace(filter.Keyword))
        {
            conditions.Add("(p.name ILIKE @Keyword OR p.code ILIKE @Keyword)");
            parameters.Add("Keyword", $"%{filter.Keyword.Trim()}%");
        }

        if (filter.ProvinceId is not null)
        {
            conditions.Add("p.province_id = @ProvinceId");
            parameters.Add("ProvinceId", filter.ProvinceId);
        }

        if (filter.DistrictId is not null)
        {
            conditions.Add("p.district_id = @DistrictId");
            parameters.Add("DistrictId", filter.DistrictId);
        }

        if (filter.Status is not null)
        {
            conditions.Add("p.status = @Status");
            parameters.Add("Status", filter.Status.ToString());
        }

        var where = " WHERE " + string.Join(" AND ", conditions);
        var sortColumn = SortColumns.GetValueOrDefault(filter.SortBy ?? string.Empty, "p.created_at");
        var direction = filter.Descending ? "DESC" : "ASC";

        parameters.Add("Limit", filter.PageSize);
        parameters.Add("Offset", (filter.Page - 1) * filter.PageSize);

        var sql = $"""
            SELECT COUNT(*) FROM realestate.projects p{where};
            {SelectColumns}{where}
            ORDER BY {sortColumn} {direction}, p.id
            LIMIT @Limit OFFSET @Offset;
            """;

        var connection = context.Database.GetDbConnection();
        using var results = await connection.QueryMultipleAsync(
            new CommandDefinition(sql, parameters, cancellationToken: cancellationToken));

        var totalCount = await results.ReadSingleAsync<int>();
        var items = (await results.ReadAsync<ProjectReadModel>()).AsList();
        return (items, totalCount);
    }
}
