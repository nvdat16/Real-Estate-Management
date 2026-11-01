using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands;

public sealed record ApproveListingCommand(Guid Id, Guid ReviewerId) : IRequest<ListingResponse>;
