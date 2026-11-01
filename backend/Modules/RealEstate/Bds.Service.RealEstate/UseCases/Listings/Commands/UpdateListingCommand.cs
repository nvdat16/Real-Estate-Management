using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands;

public sealed record UpdateListingCommand(
    Guid Id,
    Guid UserId,
    string Type,
    decimal Price,
    string Title,
    string Description,
    IReadOnlyList<string> ImageUrls) : IRequest<ListingResponse>, IListingContent;
