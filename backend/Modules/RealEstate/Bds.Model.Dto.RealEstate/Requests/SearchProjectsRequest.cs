namespace Bds.Model.Dto.RealEstate.Requests;

public sealed class SearchProjectsRequest
{
    public string? Keyword { get; init; }

    public Guid? ProvinceId { get; init; }

    public Guid? DistrictId { get; init; }

    public string? Status { get; init; }

    public string? SortBy { get; init; }

    public bool Descending { get; init; } = true;

    public int Page { get; init; } = 1;

    public int PageSize { get; init; } = 20;
}
