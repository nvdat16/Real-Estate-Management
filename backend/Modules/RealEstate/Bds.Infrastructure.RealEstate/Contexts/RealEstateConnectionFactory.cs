using System.Data.Common;
using Bds.Infrastructure.RealEstate.Interfaces;
using Dapper;
using Npgsql;

namespace Bds.Infrastructure.RealEstate.Contexts;

public sealed class RealEstateConnectionFactory : IRealEstateConnectionFactory, IDisposable
{
    private readonly NpgsqlDataSource _dataSource;

    static RealEstateConnectionFactory()
    {
        // Lets Dapper map snake_case columns returned by the fn_* functions (province_id) to PascalCase properties.
        DefaultTypeMap.MatchNamesWithUnderscores = true;
    }

    public RealEstateConnectionFactory(string connectionString)
    {
        _dataSource = NpgsqlDataSource.Create(connectionString);
    }

    public async Task<DbConnection> OpenAsync(CancellationToken cancellationToken) =>
        await _dataSource.OpenConnectionAsync(cancellationToken);

    public void Dispose() => _dataSource.Dispose();
}
