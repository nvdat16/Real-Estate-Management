using Bds.Domain.RealEstate.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bds.Infrastructure.RealEstate.Contexts.Configurations;

public sealed class PropertyConfiguration : IEntityTypeConfiguration<Property>
{
    public void Configure(EntityTypeBuilder<Property> builder)
    {
        builder.ToTable(t =>
        {
            t.HasCheckConstraint("ck_properties_area_positive", "area > 0");
            t.HasCheckConstraint("ck_properties_bedrooms_non_negative", "bedrooms >= 0");
        });

        builder.HasKey(p => p.Id);
        builder.Property(p => p.Id).ValueGeneratedNever();

        builder.Property(p => p.Code).HasMaxLength(50).IsRequired();
        // A code only has to be unique inside its project; deleted properties release their code.
        builder.HasIndex(p => new { p.ProjectId, p.Code }).IsUnique().HasFilter("is_deleted = false");

        builder.Property(p => p.Area).HasPrecision(10, 2);
        builder.Property(p => p.Position).HasMaxLength(100).IsRequired();
        builder.Property(p => p.Direction).HasConversion<string>().HasMaxLength(20);
        builder.Property(p => p.Status).HasConversion<string>().HasMaxLength(20);

        builder.HasQueryFilter(p => !p.IsDeleted);

        builder.HasOne<Project>()
            .WithMany()
            .HasForeignKey(p => p.ProjectId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
