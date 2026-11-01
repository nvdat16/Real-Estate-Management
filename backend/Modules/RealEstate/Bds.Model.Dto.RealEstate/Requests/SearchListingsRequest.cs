namespace Bds.Model.Dto.RealEstate.Requests;

public sealed class SearchListingsRequest : PagedRequest
{
    public string? Keyword { get; init; }

    public string? Status { get; init; }

    public string? Type { get; init; }
}
