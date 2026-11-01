using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands;

public sealed record DeleteListingCommand(Guid Id, Guid UserId) : IRequest;
