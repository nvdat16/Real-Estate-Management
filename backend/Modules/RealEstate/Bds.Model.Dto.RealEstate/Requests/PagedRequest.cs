namespace Bds.Model.Dto.RealEstate.Requests;

public abstract class PagedRequest
{
    public string? SortBy { get; init; }

    public bool Descending { get; init; } = true;

    public int Page { get; init; } = 1;

    public int PageSize { get; init; } = 20;
}
