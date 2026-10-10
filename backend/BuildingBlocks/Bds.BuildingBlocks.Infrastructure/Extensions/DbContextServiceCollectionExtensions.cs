using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

namespace Bds.BuildingBlocks.Infrastructure.Extensions;

public static class DbContextServiceCollectionExtensions
{
    public const string ConnectionStringName = "Default";

    // Each module keeps its tables and migration history inside its own PostgreSQL schema.
    public static IServiceCollection AddModuleDbContext<TContext>(
        this IServiceCollection services,
        string connectionString,
        string schema)
        where TContext : DbContext
    {
        services.AddDbContext<TContext>(options => options.UseNpgsql(
            connectionString,
            npgsql => npgsql.MigrationsHistoryTable("__EFMigrationsHistory", schema))
            .UseSnakeCaseNamingConvention());

        return services;
    }
}
