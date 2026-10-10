using Bds.Service.Storage.Extensions;
using Microsoft.Extensions.DependencyInjection;

namespace Bds.Presentation.Storage.Extensions;

public static class StoragePresentationExtensions
{
    public static IServiceCollection AddStorageModule(this IServiceCollection services)
    {
        services.AddControllers().AddApplicationPart(typeof(StoragePresentationExtensions).Assembly);
        services.AddStorageService();
        return services;
    }
}
