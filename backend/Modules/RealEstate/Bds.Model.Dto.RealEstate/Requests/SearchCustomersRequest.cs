namespace Bds.Model.Dto.RealEstate.Requests;

public sealed class SearchCustomersRequest : PagedRequest
{
    public string? Keyword { get; init; }
}
