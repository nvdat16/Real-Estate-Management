using Bds.BuildingBlocks.Application.Models;
using Bds.Domain.RealEstate.Enums;

namespace Bds.Infrastructure.RealEstate.ReadModels;

public sealed record PropertyFilter(
    string? Keyword,
    Guid? ProjectId,
    PropertyStatus? Status,
    Direction? Direction,
    decimal? MinArea,
    decimal? MaxArea,
    int? Bedrooms,
    PageOptions Paging);
