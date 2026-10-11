using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.Interfaces;
using MediatR;

namespace Bds.Service.RealEstate.UseCases.Locations.Queries.Handlers;

public sealed class GetProvincesHandler(ILocationService locationService)
    : IRequestHandler<GetProvincesQuery, IReadOnlyList<ProvinceResponse>>
{
    public Task<IReadOnlyList<ProvinceResponse>> Handle(GetProvincesQuery request, CancellationToken cancellationToken) =>
        locationService.GetProvincesAsync(request, cancellationToken);
}
