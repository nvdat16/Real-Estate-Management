using Bds.Domain.RealEstate.Enums;

namespace Bds.Infrastructure.RealEstate.ReadModels;

public class ListingReadModel
{
    public Guid Id { get; init; }

    public ListingType Type { get; init; }

    public decimal Price { get; init; }

    public string Title { get; init; } = null!;

    public string Description { get; init; } = null!;

    public string[] ImageUrls { get; init; } = [];

    public ListingStatus Status { get; init; }

    public string? RejectionReason { get; init; }

    public DateTime? ReviewedAt { get; init; }

    public DateTime? SubmittedAt { get; init; }

    public DateTime CreatedAt { get; init; }

    public DateTime? UpdatedAt { get; init; }

    // Approved listing of an available, non-deleted property: visible to everyone.
    public bool IsPublic { get; init; }

    public Guid PropertyId { get; init; }

    public string PropertyCode { get; init; } = null!;

    public decimal Area { get; init; }

    public int Floor { get; init; }

    public int Bedrooms { get; init; }

    public Direction Direction { get; init; }

    public Guid ProjectId { get; init; }

    public string ProjectName { get; init; } = null!;

    public string ProvinceName { get; init; } = null!;

    public string DistrictName { get; init; } = null!;

    public Guid AgentId { get; init; }

    public Guid AgentUserId { get; init; }

    public string AgentName { get; init; } = null!;

    public string AgentPhoneNumber { get; init; } = null!;
}
