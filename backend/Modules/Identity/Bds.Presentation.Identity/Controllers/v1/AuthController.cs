using System.Security.Claims;
using Bds.BuildingBlocks.Application.Security;
using Bds.Model.Dto.Identity.Requests;
using Bds.Model.Dto.Identity.Responses;
using Bds.Service.Identity.UseCases.Auth.Commands;
using Bds.Service.Identity.UseCases.Auth.Queries;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;

namespace Bds.Presentation.Identity.Controllers.v1;

[ApiController]
[Route("api/v1/auth")]
public sealed class AuthController(IMediator mediator) : ControllerBase
{
    [HttpPost("register")]
    [AllowAnonymous]
    public async Task<ActionResult<UserResponse>> Register(RegisterRequest request, CancellationToken cancellationToken)
    {
        var command = new RegisterCommand(request.Email, request.Password, request.FullName, request.PhoneNumber);
        var user = await mediator.Send(command, cancellationToken);

        return StatusCode(StatusCodes.Status201Created, user);
    }

    [HttpPost("login")]
    [AllowAnonymous]
    public async Task<ActionResult<AuthResponse>> Login(LoginRequest request, CancellationToken cancellationToken) =>
        await mediator.Send(new LoginCommand(request.Email, request.Password), cancellationToken);

    [HttpGet("me")]
    [Authorize]
    public async Task<ActionResult<UserResponse>> Me(CancellationToken cancellationToken)
    {
        var userId = Guid.Parse(User.FindFirstValue(CustomClaimTypes.UserId)!);
        return await mediator.Send(new GetCurrentUserQuery(userId), cancellationToken);
    }
}