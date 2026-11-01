using Bds.BuildingBlocks.Application.Models;
using Bds.Domain.RealEstate.Enums;

namespace Bds.Infrastructure.RealEstate.ReadModels;

// PublicOnly limits results to approved listings of available properties; AgentUserId limits them to one agent.
public sealed record ListingFilter(
    bool PublicOnly,
    Guid? AgentUserId,
    ListingStatus? Status,
    string? Keyword,
    ListingType? Type,
    decimal? MinPrice,
    decimal? MaxPrice,
    Guid? ProvinceId,
    Guid? DistrictId,
    Guid? ProjectId,
    decimal? MinArea,
    decimal? MaxArea,
    int? Bedrooms,
    PageOptions Paging);
