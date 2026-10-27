using Bds.BuildingBlocks.Application.Models;

namespace Bds.Infrastructure.RealEstate.ReadModels;

public sealed record ProfileFilter(string? Keyword, PageOptions Paging);
