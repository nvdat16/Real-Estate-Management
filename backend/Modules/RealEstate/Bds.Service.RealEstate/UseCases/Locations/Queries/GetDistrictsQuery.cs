using Bds.Model.Dto.RealEstate.Responses;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Locations.Queries;

public sealed record GetDistrictsQuery(Guid ProvinceId) : IRequest<IReadOnlyList<DistrictResponse>>;
