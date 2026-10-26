using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.ReadModels;
using Dapper;

namespace Bds.Infrastructure.RealEstate.Repositories;

public sealed class LocationRepository(IRealEstateConnectionFactory connectionFactory) : ILocationRepository
{
    public async Task<IReadOnlyList<ProvinceReadModel>> GetProvincesAsync(CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        var rows = await connection.QueryAsync<ProvinceReadModel>(new CommandDefinition(
            "SELECT * FROM realestate.fn_location_get_provinces()",
            cancellationToken: cancellationToken));
        return rows.AsList();
    }

    public async Task<IReadOnlyList<DistrictReadModel>> GetDistrictsAsync(Guid provinceId, CancellationToken cancellationToken)
    {
        await using var connection = await connectionFactory.OpenAsync(cancellationToken);
        var rows = await connection.QueryAsync<DistrictReadModel>(new CommandDefinition(
            "SELECT * FROM realestate.fn_location_get_districts(@ProvinceId)",
            new { ProvinceId = provinceId },
            cancellationToken: cancellationToken));
        return rows.AsList();
    }
}
