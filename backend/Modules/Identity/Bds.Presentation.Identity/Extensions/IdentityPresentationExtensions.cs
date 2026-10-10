using Bds.Service.Identity.Extensions;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace Bds.Presentation.Identity.Extensions;

public static class IdentityPresentationExtensions
{
    public static IServiceCollection AddIdentityModule(this IServiceCollection services, IConfiguration configuration)
    {
        services.AddControllers().AddApplicationPart(typeof(IdentityPresentationExtensions).Assembly);
        services.AddIdentityService(configuration);
        return services;
    }
}
