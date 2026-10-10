using Microsoft.EntityFrameworkCore;

namespace Bds.Infrastructure.RealEstate.Contexts;

public sealed class RealEstateContext(DbContextOptions<RealEstateContext> options) : DbContext(options)
{
    public const string Schema = "realestate";

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.HasDefaultSchema(Schema);
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(RealEstateContext).Assembly);
    }
}
