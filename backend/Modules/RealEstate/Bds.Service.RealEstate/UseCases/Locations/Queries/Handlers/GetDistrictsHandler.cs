using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Locations.Queries.Handlers;

public sealed class GetDistrictsHandler(ILocationService locationService)
    : IRequestHandler<GetDistrictsQuery, IReadOnlyList<DistrictResponse>>
{
    public Task<IReadOnlyList<DistrictResponse>> Handle(GetDistrictsQuery request, CancellationToken cancellationToken) =>
        locationService.GetDistrictsAsync(request, cancellationToken);
}
