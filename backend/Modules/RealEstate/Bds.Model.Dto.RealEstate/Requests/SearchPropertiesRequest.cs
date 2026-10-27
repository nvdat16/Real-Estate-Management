namespace Bds.Model.Dto.RealEstate.Requests;

public sealed class SearchPropertiesRequest : PagedRequest
{
    public string? Keyword { get; init; }

    public Guid? ProjectId { get; init; }

    public string? Status { get; init; }

    public string? Direction { get; init; }

    public decimal? MinArea { get; init; }

    public decimal? MaxArea { get; init; }

    public int? Bedrooms { get; init; }
}
