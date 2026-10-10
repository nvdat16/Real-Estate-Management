using Bds.Model.Dto.Identity.Responses;
using Bds.Service.Identity.Interfaces;
using MediatR;

namespace Bds.Service.Identity.UseCases.Auth.Commands.Handlers;

public sealed class LoginHandler(IAuthService authService) : IRequestHandler<LoginCommand, AuthResponse>
{
    public Task<AuthResponse> Handle(LoginCommand request, CancellationToken cancellationToken) =>
        authService.LoginAsync(request, cancellationToken);
}