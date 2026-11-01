using Bds.Domain.RealEstate.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bds.Infrastructure.RealEstate.Contexts.Configurations;

public sealed class ListingConfiguration : IEntityTypeConfiguration<Listing>
{
    public void Configure(EntityTypeBuilder<Listing> builder)
    {
        builder.ToTable(t => t.HasCheckConstraint("ck_listings_price_positive", "price > 0"));

        builder.HasKey(l => l.Id);
        builder.Property(l => l.Id).ValueGeneratedNever();

        builder.Property(l => l.Type).HasConversion<string>().HasMaxLength(20);
        builder.Property(l => l.Price).HasPrecision(18, 0);
        builder.Property(l => l.Title).HasMaxLength(200).IsRequired();
        builder.Property(l => l.Description).HasMaxLength(5000).IsRequired();
        builder.Property(l => l.ImageUrls).HasColumnType("text[]");
        builder.Property(l => l.Status).HasConversion<string>().HasMaxLength(20);
        builder.Property(l => l.RejectionReason).HasMaxLength(500);

        // RULE-02: a property has at most one listing waiting for review or approved.
        builder.HasIndex(l => l.PropertyId)
            .IsUnique()
            .HasFilter("status IN ('PendingReview', 'Approved') AND is_deleted = false")
            .HasDatabaseName("ix_listings_property_id_active");

        builder.HasIndex(l => l.AgentId);
        builder.HasIndex(l => new { l.Status, l.Type, l.Price });

        builder.HasQueryFilter(l => !l.IsDeleted);

        builder.HasOne<Property>()
            .WithMany()
            .HasForeignKey(l => l.PropertyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<Agent>()
            .WithMany()
            .HasForeignKey(l => l.AgentId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
