using Bds.BuildingBlocks.Application.Models;
using Bds.Domain.RealEstate.Enums;

namespace Bds.Infrastructure.RealEstate.ReadModels;

public sealed record ProjectFilter(
    string? Keyword,
    Guid? ProvinceId,
    Guid? DistrictId,
    ProjectStatus? Status,
    PageOptions Paging);
