using Bds.Service.RealEstate.Extensions;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace Bds.Presentation.RealEstate.Extensions;

public static class RealEstatePresentationExtensions
{
    public static IServiceCollection AddRealEstateModule(this IServiceCollection services, IConfiguration configuration)
    {
        services.AddControllers().AddApplicationPart(typeof(RealEstatePresentationExtensions).Assembly);
        services.AddRealEstateService(configuration);
        return services;
    }
}
