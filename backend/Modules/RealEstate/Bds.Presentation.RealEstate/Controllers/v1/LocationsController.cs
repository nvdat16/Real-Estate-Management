using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.UseCases.Locations.Queries;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bds.Presentation.RealEstate.Controllers.v1;

[ApiController]
[Route("api/v1/locations")]
[AllowAnonymous]
public sealed class LocationsController(IMediator mediator) : ControllerBase
{
    [HttpGet("provinces")]
    public async Task<ActionResult<IReadOnlyList<ProvinceResponse>>> GetProvinces(CancellationToken cancellationToken) =>
        Ok(await mediator.Send(new GetProvincesQuery(), cancellationToken));

    [HttpGet("provinces/{provinceId:guid}/districts")]
    public async Task<ActionResult<IReadOnlyList<DistrictResponse>>> GetDistricts(Guid provinceId, CancellationToken cancellationToken) =>
        Ok(await mediator.Send(new GetDistrictsQuery(provinceId), cancellationToken));
}
