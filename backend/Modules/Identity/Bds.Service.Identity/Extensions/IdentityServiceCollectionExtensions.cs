using Bds.BuildingBlocks.Infrastructure.Extensions;
using Bds.Infrastructure.Identity.Contexts;
using Bds.Infrastructure.Identity.Interfaces;
using Bds.Infrastructure.Identity.Repositories;
using Bds.Infrastructure.Identity.Security;
using Bds.Infrastructure.Identity.UnitOfWorks;
using Bds.Service.Identity.Helpers;
using Bds.Service.Identity.Interfaces;
using Bds.Service.Identity.Services;
using FluentValidation;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace Bds.Service.Identity.Extensions;

public static class IdentityServiceCollectionExtensions
{
    public static IServiceCollection AddIdentityService(this IServiceCollection services, IConfiguration configuration)
    {
        var connectionString = configuration.GetConnectionString(DbContextServiceCollectionExtensions.ConnectionStringName)
            ?? throw new InvalidOperationException("Connection string 'Default' is not configured.");

        services.AddModuleDbContext<IdentityContext>(connectionString, IdentityContext.Schema);
        services.AddScoped<IIdentityUnitOfWork, IdentityUnitOfWork>();
        services.AddScoped<IUserRepository, UserRepository>();
        services.AddScoped<IRoleRepository, RoleRepository>();
        services.AddSingleton<IPasswordHasher, PasswordHasher>();
        services.AddSingleton<IJwtTokenGenerator, JwtTokenGenerator>();
        services.AddScoped<IAuthService, AuthService>();

        var assembly = typeof(IdentityServiceCollectionExtensions).Assembly;
        services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(assembly));
        services.AddValidatorsFromAssembly(assembly);

        return services;
    }
}
