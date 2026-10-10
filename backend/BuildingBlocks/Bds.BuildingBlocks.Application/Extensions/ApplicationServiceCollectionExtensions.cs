using Bds.BuildingBlocks.Application.Behaviors;
using MediatR;
using Microsoft.Extensions.DependencyInjection;

namespace Bds.BuildingBlocks.Application.Extensions;

public static class ApplicationServiceCollectionExtensions
{
    // Registered once by the host so the behavior does not run multiple times per request.
    public static IServiceCollection AddBuildingBlocksApplication(this IServiceCollection services)
    {
        services.AddTransient(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));
        return services;
    }
}
