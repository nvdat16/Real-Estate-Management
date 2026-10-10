using Bds.Model.Dto.Identity.Responses;
using Bds.Service.Identity.Interfaces;
using MediatR;

namespace Bds.Service.Identity.UseCases.Auth.Commands.Handlers;

public sealed class RegisterHandler(IAuthService authService) : IRequestHandler<RegisterCommand, UserResponse>
{
    public Task<UserResponse> Handle(RegisterCommand request, CancellationToken cancellationToken) =>
        authService.RegisterAsync(request, cancellationToken);
}