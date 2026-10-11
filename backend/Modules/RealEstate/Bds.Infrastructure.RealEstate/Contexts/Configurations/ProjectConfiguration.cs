using Bds.Domain.RealEstate.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bds.Infrastructure.RealEstate.Contexts.Configurations;

public sealed class ProjectConfiguration : IEntityTypeConfiguration<Project>
{
    public void Configure(EntityTypeBuilder<Project> builder)
    {
        builder.HasKey(p => p.Id);
        builder.Property(p => p.Id).ValueGeneratedNever();

        builder.Property(p => p.Code).HasMaxLength(50).IsRequired();
        // Deleted projects release their code so it can be reused.
        builder.HasIndex(p => p.Code).IsUnique().HasFilter("is_deleted = false");

        builder.Property(p => p.Name).HasMaxLength(200).IsRequired();
        builder.Property(p => p.AddressLine).HasMaxLength(300).IsRequired();
        builder.Property(p => p.Developer).HasMaxLength(200).IsRequired();
        builder.Property(p => p.Status).HasConversion<string>().HasMaxLength(20);

        builder.HasQueryFilter(p => !p.IsDeleted);

        builder.HasOne<Province>()
            .WithMany()
            .HasForeignKey(p => p.ProvinceId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<District>()
            .WithMany()
            .HasForeignKey(p => p.DistrictId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
