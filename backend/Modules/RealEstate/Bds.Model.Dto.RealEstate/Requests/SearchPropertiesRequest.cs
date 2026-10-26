namespace Bds.Model.Dto.RealEstate.Requests;

public sealed class SearchPropertiesRequest
{
    public string? Keyword { get; init; }

    public Guid? ProjectId { get; init; }

    public string? Status { get; init; }

    public string? Direction { get; init; }

    public decimal? MinArea { get; init; }

    public decimal? MaxArea { get; init; }

    public int? Bedrooms { get; init; }

    public string? SortBy { get; init; }

    public bool Descending { get; init; } = true;

    public int Page { get; init; } = 1;

    public int PageSize { get; init; } = 20;
}
