using Bds.Infrastructure.RealEstate.ReadModels;
using Bds.Model.Dto.RealEstate.Responses;

namespace Bds.Service.RealEstate.UseCases.Listings;

public static class ListingMapping
{
    public static ListingResponse ToResponse(ListingReadModel listing) => new(
        listing.Id,
        listing.Type.ToString(),
        listing.Price,
        listing.Title,
        listing.Description,
        listing.ImageUrls,
        listing.Status.ToString(),
        listing.RejectionReason,
        listing.SubmittedAt,
        listing.ReviewedAt,
        listing.CreatedAt,
        listing.UpdatedAt,
        listing.PropertyId,
        listing.PropertyCode,
        listing.Area,
        listing.Floor,
        listing.Bedrooms,
        listing.Direction.ToString(),
        listing.ProjectId,
        listing.ProjectName,
        listing.ProvinceName,
        listing.DistrictName,
        listing.AgentId,
        listing.AgentName,
        listing.AgentPhoneNumber);
}
