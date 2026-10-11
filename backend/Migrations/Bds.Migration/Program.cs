using Bds.BuildingBlocks.Infrastructure.Extensions;
using Bds.Infrastructure.Identity.Contexts;
using Bds.Infrastructure.Identity.Security;
using Bds.Infrastructure.Identity.Seed;
using Bds.Infrastructure.RealEstate.Contexts;
using Bds.Infrastructure.RealEstate.Seed;
using Microsoft.EntityFrameworkCore;

var builder = Host.CreateApplicationBuilder(args);

var connectionString = builder.Configuration.GetConnectionString(DbContextServiceCollectionExtensions.ConnectionStringName);
if (string.IsNullOrWhiteSpace(connectionString))
{
    throw new InvalidOperationException("Connection string 'Default' is not configured.");
}

builder.Services.AddModuleDbContext<IdentityContext>(connectionString, IdentityContext.Schema);
builder.Services.AddModuleDbContext<RealEstateContext>(connectionString, RealEstateContext.Schema);

using var host = builder.Build();
using var scope = host.Services.CreateScope();
var services = scope.ServiceProvider;

await services.GetRequiredService<IdentityContext>().Database.MigrateAsync();
await services.GetRequiredService<RealEstateContext>().Database.MigrateAsync();

var adminEmail = builder.Configuration["Seed:AdminEmail"];
var adminPassword = builder.Configuration["Seed:AdminPassword"];
if (string.IsNullOrWhiteSpace(adminEmail) || string.IsNullOrWhiteSpace(adminPassword))
{
    throw new InvalidOperationException("Seed:AdminEmail and Seed:AdminPassword must be configured.");
}

await IdentitySeeder.SeedAsync(services.GetRequiredService<IdentityContext>(), new PasswordHasher(), adminEmail, adminPassword);
await RealEstateSeeder.SeedAsync(services.GetRequiredService<RealEstateContext>());
