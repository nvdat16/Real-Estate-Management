using FluentValidation;
using Microsoft.Extensions.DependencyInjection;

namespace Bds.Service.Storage.Extensions;

public static class StorageServiceCollectionExtensions
{
    public static IServiceCollection AddStorageService(this IServiceCollection services)
    {
        var assembly = typeof(StorageServiceCollectionExtensions).Assembly;
        services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(assembly));
        services.AddValidatorsFromAssembly(assembly);

        return services;
    }
}
