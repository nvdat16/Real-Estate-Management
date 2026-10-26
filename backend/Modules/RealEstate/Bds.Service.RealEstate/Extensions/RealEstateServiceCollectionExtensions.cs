using Bds.BuildingBlocks.Infrastructure.Extensions;
using Bds.Infrastructure.RealEstate.Contexts;
using Bds.Infrastructure.RealEstate.Interfaces;
using Bds.Infrastructure.RealEstate.Repositories;
using Bds.Service.RealEstate.Interfaces;
using Bds.Service.RealEstate.Services;
using FluentValidation;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace Bds.Service.RealEstate.Extensions;

public static class RealEstateServiceCollectionExtensions
{
    public static IServiceCollection AddRealEstateService(this IServiceCollection services, IConfiguration configuration)
    {
        var connectionString = configuration.GetConnectionString(DbContextServiceCollectionExtensions.ConnectionStringName)
            ?? throw new InvalidOperationException("Connection string 'Default' is not configured.");

        services.AddSingleton<IRealEstateConnectionFactory>(_ => new RealEstateConnectionFactory(connectionString));
        services.AddScoped<IProjectRepository, ProjectRepository>();
        services.AddScoped<ILocationRepository, LocationRepository>();
        services.AddScoped<IPropertyRepository, PropertyRepository>();
        services.AddScoped<ILocationService, LocationService>();
        services.AddScoped<IProjectService, ProjectService>();
        services.AddScoped<IPropertyService, PropertyService>();

        var assembly = typeof(RealEstateServiceCollectionExtensions).Assembly;
        services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(assembly));
        services.AddValidatorsFromAssembly(assembly);

        return services;
    }
}
