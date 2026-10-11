using Bds.Infrastructure.RealEstate.Contexts;
using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.ReadModels;
using Dapper;
using Microsoft.EntityFrameworkCore;

namespace Bds.Infrastructure.RealEstate.Repositories;

public sealed class LocationQueryRepository(RealEstateContext context) : ILocationQueryRepository
{
    public async Task<IReadOnlyList<ProvinceReadModel>> GetProvincesAsync(CancellationToken cancellationToken)
    {
        const string sql = """
            SELECT id AS Id, code AS Code, name AS Name
            FROM realestate.provinces
            ORDER BY name
            """;

        var connection = context.Database.GetDbConnection();
        var rows = await connection.QueryAsync<ProvinceReadModel>(new CommandDefinition(sql, cancellationToken: cancellationToken));
        return rows.AsList();
    }

    public async Task<IReadOnlyList<DistrictReadModel>> GetDistrictsAsync(Guid provinceId, CancellationToken cancellationToken)
    {
        const string sql = """
            SELECT id AS Id, province_id AS ProvinceId, code AS Code, name AS Name
            FROM realestate.districts
            WHERE province_id = @ProvinceId
            ORDER BY name
            """;

        var connection = context.Database.GetDbConnection();
        var rows = await connection.QueryAsync<DistrictReadModel>(
            new CommandDefinition(sql, new { ProvinceId = provinceId }, cancellationToken: cancellationToken));
        return rows.AsList();
    }

    public Task<bool> DistrictBelongsToProvinceAsync(Guid districtId, Guid provinceId, CancellationToken cancellationToken)
    {
        const string sql = """
            SELECT EXISTS (
                SELECT 1 FROM realestate.districts
                WHERE id = @DistrictId AND province_id = @ProvinceId)
            """;

        var connection = context.Database.GetDbConnection();
        return connection.ExecuteScalarAsync<bool>(
            new CommandDefinition(sql, new { DistrictId = districtId, ProvinceId = provinceId }, cancellationToken: cancellationToken));
    }
}
