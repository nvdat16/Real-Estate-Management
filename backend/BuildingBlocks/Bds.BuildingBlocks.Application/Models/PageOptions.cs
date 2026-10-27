namespace Bds.BuildingBlocks.Application.Models;

public sealed record PageOptions(int Page, int PageSize, string? SortBy, bool Descending)
{
    public const int MaxPageSize = 100;

    public int Offset => (Page - 1) * PageSize;
}
