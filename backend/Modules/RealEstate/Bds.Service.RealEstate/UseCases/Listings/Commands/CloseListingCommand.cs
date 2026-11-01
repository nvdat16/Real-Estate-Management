using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands;

public sealed record CloseListingCommand(Guid Id, Guid UserId, bool CanCloseAny) : IRequest<ListingResponse>;
