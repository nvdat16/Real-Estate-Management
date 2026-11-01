using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands;

public sealed record SubmitListingCommand(Guid Id, Guid UserId) : IRequest<ListingResponse>;
