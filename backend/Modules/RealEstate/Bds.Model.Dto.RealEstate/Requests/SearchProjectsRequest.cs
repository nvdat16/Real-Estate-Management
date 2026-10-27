namespace Bds.Model.Dto.RealEstate.Requests;

public sealed class SearchProjectsRequest : PagedRequest
{
    public string? Keyword { get; init; }

    public Guid? ProvinceId { get; init; }

    public Guid? DistrictId { get; init; }

    public string? Status { get; init; }
}
