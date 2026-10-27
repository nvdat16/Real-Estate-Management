using Bds.Domain.RealEstate.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bds.Infrastructure.RealEstate.Contexts.Configurations;

public sealed class AgentConfiguration : IEntityTypeConfiguration<Agent>
{
    public void Configure(EntityTypeBuilder<Agent> builder)
    {
        builder.HasKey(a => a.Id);
        builder.Property(a => a.Id).ValueGeneratedNever();

        // UserId points to identity.users by value only; modules never share foreign keys.
        builder.HasIndex(a => a.UserId).IsUnique();

        builder.Property(a => a.FullName).HasMaxLength(200).IsRequired();
        builder.Property(a => a.Email).HasMaxLength(256).IsRequired();
        builder.Property(a => a.PhoneNumber).HasMaxLength(20).IsRequired();

        builder.Property(a => a.LicenseNumber).HasMaxLength(50);
        builder.HasIndex(a => a.LicenseNumber).IsUnique().HasFilter("license_number IS NOT NULL");
    }
}
