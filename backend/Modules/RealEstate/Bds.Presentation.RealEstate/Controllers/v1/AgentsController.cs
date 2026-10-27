using Bds.BuildingBlocks.Application.Models;
using Bds.BuildingBlocks.Application.Security;
using Bds.Model.Dto.RealEstate.Requests;
using Bds.Model.Dto.RealEstate.Responses;
using Bds.Service.RealEstate.UseCases.Agents.Commands;
using Bds.Service.RealEstate.UseCases.Agents.Queries;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bds.Presentation.RealEstate.Controllers.v1;

[ApiController]
[Route("api/v1/agents")]
public sealed class AgentsController(IMediator mediator) : ControllerBase
{
    [HttpGet("me")]
    [Authorize(Policy = Permissions.ProfileAgent)]
    public async Task<ActionResult<AgentResponse>> GetMe(CancellationToken cancellationToken) =>
        await mediator.Send(new GetMyAgentProfileQuery(User.GetUserId()), cancellationToken);

    [HttpPut("me")]
    [Authorize(Policy = Permissions.ProfileAgent)]
    public async Task<ActionResult<AgentResponse>> UpsertMe(UpsertAgentProfileRequest request, CancellationToken cancellationToken)
    {
        var command = new UpsertAgentProfileCommand(
            User.GetUserId(), User.GetEmail(), request.FullName, request.PhoneNumber, request.LicenseNumber);
        return await mediator.Send(command, cancellationToken);
    }

    [HttpGet]
    [Authorize(Policy = Permissions.AgentsManage)]
    public async Task<ActionResult<PagedResult<AgentResponse>>> Search(
        [FromQuery] SearchAgentsRequest request,
        CancellationToken cancellationToken)
    {
        var paging = new PageOptions(request.Page, request.PageSize, request.SortBy, request.Descending);
        return await mediator.Send(new SearchAgentsQuery(request.Keyword, paging), cancellationToken);
    }

    [HttpGet("{id:guid}")]
    [Authorize(Policy = Permissions.AgentsManage)]
    public async Task<ActionResult<AgentResponse>> GetById(Guid id, CancellationToken cancellationToken) =>
        await mediator.Send(new GetAgentByIdQuery(id), cancellationToken);
}
