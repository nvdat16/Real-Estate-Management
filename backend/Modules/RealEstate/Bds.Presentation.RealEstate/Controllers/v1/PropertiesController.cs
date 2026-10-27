using Bds.BuildingBlocks.Application.Models;
using Bds.BuildingBlocks.Application.Security;
using Bds.Model.Dto.RealEstate.Requests;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.UseCases.Properties.Commands;
using Bds.Service.RealEstate.UseCases.Properties.Queries;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bds.Presentation.RealEstate.Controllers.v1;

[ApiController]
[Route("api/v1/properties")]
public sealed class PropertiesController(IMediator mediator) : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<PagedResult<PropertyResponse>>> Search(
        [FromQuery] SearchPropertiesRequest request,
        CancellationToken cancellationToken)
    {
        var paging = new PageOptions(request.Page, request.PageSize, request.SortBy, request.Descending);
        var query = new SearchPropertiesQuery(
            request.Keyword, request.ProjectId, request.Status, request.Direction, request.MinArea, request.MaxArea,
            request.Bedrooms, paging);
        return await mediator.Send(query, cancellationToken);
    }

    [HttpGet("{id:guid}")]
    public async Task<ActionResult<PropertyResponse>> GetById(Guid id, CancellationToken cancellationToken) =>
        await mediator.Send(new GetPropertyByIdQuery(id), cancellationToken);

    [HttpPost]
    [Authorize(Policy = Permissions.ProjectsManage)]
    public async Task<ActionResult<PropertyResponse>> Create(CreatePropertyRequest request, CancellationToken cancellationToken)
    {
        var command = new CreatePropertyCommand(
            request.ProjectId, request.Code, request.Area, request.Floor, request.Position, request.Bedrooms, request.Direction);
        var property = await mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetById), new { id = property.Id }, property);
    }

    [HttpPut("{id:guid}")]
    [Authorize(Policy = Permissions.ProjectsManage)]
    public async Task<ActionResult<PropertyResponse>> Update(Guid id, UpdatePropertyRequest request, CancellationToken cancellationToken)
    {
        var command = new UpdatePropertyCommand(id, request.Area, request.Floor, request.Position, request.Bedrooms, request.Direction);
        return await mediator.Send(command, cancellationToken);
    }

    [HttpDelete("{id:guid}")]
    [Authorize(Policy = Permissions.ProjectsManage)]
    public async Task<IActionResult> Delete(Guid id, CancellationToken cancellationToken)
    {
        await mediator.Send(new DeletePropertyCommand(id), cancellationToken);
        return NoContent();
    }
}
