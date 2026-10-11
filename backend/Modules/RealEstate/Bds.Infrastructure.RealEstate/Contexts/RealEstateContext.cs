using Bds.Domain.RealEstate.Entities;
using Microsoft.EntityFrameworkCore;

namespace Bds.Infrastructure.RealEstate.Contexts;

public sealed class RealEstateContext(DbContextOptions<RealEstateContext> options) : DbContext(options)
{
    public const string Schema = "realestate";

    public DbSet<Province> Provinces => Set<Province>();

    public DbSet<District> Districts => Set<District>();

    public DbSet<Project> Projects => Set<Project>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.HasDefaultSchema(Schema);
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(RealEstateContext).Assembly);
    }
}
