using Bds.Service.Identity.Interfaces;
using MediatR;

namespace Bds.Service.Identity.UseCases.Users.Commands.Handlers;

public sealed class UnlockUserHandler(IUserService userService)
    : IRequestHandler<UnlockUserCommand>
{
    public Task Handle(UnlockUserCommand request, CancellationToken cancellationToken) =>
        userService.UnlockAsync(request, cancellationToken);
}