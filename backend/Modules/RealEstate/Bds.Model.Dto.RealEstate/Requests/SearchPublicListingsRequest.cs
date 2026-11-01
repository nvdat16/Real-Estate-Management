namespace Bds.Model.Dto.RealEstate.Requests;

public sealed class SearchPublicListingsRequest : PagedRequest
{
    public string? Keyword { get; init; }

    public string? Type { get; init; }

    public decimal? MinPrice { get; init; }

    public decimal? MaxPrice { get; init; }

    public Guid? ProvinceId { get; init; }

    public Guid? DistrictId { get; init; }

    public Guid? ProjectId { get; init; }

    public decimal? MinArea { get; init; }

    public decimal? MaxArea { get; init; }

    public int? Bedrooms { get; init; }
}
