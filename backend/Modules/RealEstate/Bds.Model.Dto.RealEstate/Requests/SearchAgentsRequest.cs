namespace Bds.Model.Dto.RealEstate.Requests;

public sealed class SearchAgentsRequest : PagedRequest
{
    public string? Keyword { get; init; }
}
