namespace Bds.Service.RealEstate.UseCases.Listings.Commands;

public interface IListingContent
{
    string Type { get; }

    decimal Price { get; }

    string Title { get; }

    string Description { get; }

    IReadOnlyList<string> ImageUrls { get; }
}
