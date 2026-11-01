using Bds.BuildingBlocks.Domain.Entities;
using Bds.Domain.RealEstate.Enums;

namespace Bds.Domain.RealEstate.Entities;

public sealed class Listing : BaseEntity, ISoftDelete
{
    private Listing()
    {
    }

    public Guid PropertyId { get; private set; }

    public Guid AgentId { get; private set; }

    public ListingType Type { get; private set; }

    // VND: the whole unit for Sale, per month for Rent.
    public decimal Price { get; private set; }

    public string Title { get; private set; } = null!;

    public string Description { get; private set; } = null!;

    public List<string> ImageUrls { get; private set; } = [];

    public ListingStatus Status { get; private set; }

    public string? RejectionReason { get; private set; }

    public Guid? ReviewedBy { get; private set; }

    public DateTime? ReviewedAt { get; private set; }

    public DateTime? SubmittedAt { get; private set; }

    public bool IsDeleted { get; private set; }

    public DateTime? DeletedAt { get; private set; }
}
