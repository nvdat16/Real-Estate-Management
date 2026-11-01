namespace Bds.Model.Dto.RealEstate.Requests;

public sealed record CreateListingRequest(
    Guid PropertyId,
    string Type,
    decimal Price,
    string Title,
    string Description,
    IReadOnlyList<string>? ImageUrls);
