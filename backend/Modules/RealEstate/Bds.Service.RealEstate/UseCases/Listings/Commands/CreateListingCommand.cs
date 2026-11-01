using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands;

public sealed record CreateListingCommand(
    Guid UserId,
    Guid PropertyId,
    string Type,
    decimal Price,
    string Title,
    string Description,
    IReadOnlyList<string> ImageUrls) : IRequest<ListingResponse>, IListingContent;
