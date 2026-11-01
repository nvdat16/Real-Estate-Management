using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Commands;

public sealed record RejectListingCommand(Guid Id, Guid ReviewerId, string Reason) : IRequest<ListingResponse>;
