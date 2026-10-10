using Bds.BuildingBlocks.Application.Security;
using Bds.Model.Dto.Identity.Requests;
using Bds.Model.Dto.Identity.Responses;
using Bds.Service.Identity.UseCases.Users.Commands;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;

namespace Bds.Presentation.Identity.Controllers.v1;

[ApiController]
[Route("api/v1/users")]
[Authorize(Policy = Permissions.UsersManage)]
public sealed class UserController(IMediator mediator): ControllerBase
{
    [HttpPost]
    public async Task<ActionResult<UserResponse>> Create(CreateUserRequest request, CancellationToken cancellationToken)
    {
        var command = new CreateUserCommand(request.Email, request.Password, request.FullName, request.PhoneNumber, request.Role);
        var user = await mediator.Send(command, cancellationToken);
        return StatusCode(StatusCodes.Status201Created, user);
    }

    [HttpPost("{id:guid}/lock")]
    public async Task<IActionResult> Lock(Guid id, CancellationToken cancellationToken)
    {
        var command = new LockUserCommand(id, User.GetUserId());
        await mediator.Send(command, cancellationToken);
        return NoContent();
    }

    [HttpPost("{id:guid}/unlock")]
    public async Task<IActionResult> Unlock(Guid id, CancellationToken cancellationToken)
    {
        var command = new UnlockUserCommand(id);
        await mediator.Send(command, cancellationToken);
        return NoContent();
    }
}