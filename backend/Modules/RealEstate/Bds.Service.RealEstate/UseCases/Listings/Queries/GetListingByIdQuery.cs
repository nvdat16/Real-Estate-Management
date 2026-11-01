using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Listings.Queries;

public sealed record GetListingByIdQuery(Guid Id, Guid? CurrentUserId, bool CanViewAll) : IRequest<ListingResponse>;
