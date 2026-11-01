namespace Bds.Model.Dto.RealEstate.Requests;

public sealed record UpdateListingRequest(
    string Type,
    decimal Price,
    string Title,
    string Description,
    IReadOnlyList<string>? ImageUrls);
