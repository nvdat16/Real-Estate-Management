using Bds.BuildingBlocks.Application.Models;
using Bds.BuildingBlocks.Application.Security;
using Bds.Model.Dto.RealEstate.Requests;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.UseCases.Projects.Commands;
using Bds.Service.RealEstate.UseCases.Projects.Queries;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bds.Presentation.RealEstate.Controllers.v1;

[ApiController]
[Route("api/v1/projects")]
public sealed class ProjectsController(IMediator mediator) : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<PagedResult<ProjectResponse>>> Search(
        [FromQuery] SearchProjectsRequest request,
        CancellationToken cancellationToken)
    {
        var paging = new PageOptions(request.Page, request.PageSize, request.SortBy, request.Descending);
        var query = new SearchProjectsQuery(request.Keyword, request.ProvinceId, request.DistrictId, request.Status, paging);
        return await mediator.Send(query, cancellationToken);
    }

    [HttpGet("{id:guid}")]
    public async Task<ActionResult<ProjectResponse>> GetById(Guid id, CancellationToken cancellationToken) =>
        await mediator.Send(new GetProjectByIdQuery(id), cancellationToken);

    [HttpPost]
    [Authorize(Policy = Permissions.ProjectsManage)]
    public async Task<ActionResult<ProjectResponse>> Create(CreateProjectRequest request, CancellationToken cancellationToken)
    {
        var command = new CreateProjectCommand(
            request.Code, request.Name, request.ProvinceId, request.DistrictId, request.AddressLine, request.Developer);
        var project = await mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetById), new { id = project.Id }, project);
    }

    [HttpPut("{id:guid}")]
    [Authorize(Policy = Permissions.ProjectsManage)]
    public async Task<ActionResult<ProjectResponse>> Update(Guid id, UpdateProjectRequest request, CancellationToken cancellationToken)
    {
        var command = new UpdateProjectCommand(
            id, request.Name, request.ProvinceId, request.DistrictId, request.AddressLine, request.Developer, request.Status);
        return await mediator.Send(command, cancellationToken);
    }

    [HttpDelete("{id:guid}")]
    [Authorize(Policy = Permissions.ProjectsManage)]
    public async Task<IActionResult> Delete(Guid id, CancellationToken cancellationToken)
    {
        await mediator.Send(new DeleteProjectCommand(id), cancellationToken);
        return NoContent();
    }
}
