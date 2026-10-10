using Bds.Service.Identity.Interfaces;
using MediatR;

namespace Bds.Service.Identity.UseCases.Users.Commands.Handlers;

public sealed class LockUserHandler(IUserService userService)
    : IRequestHandler<LockUserCommand>
{
    public Task Handle(LockUserCommand request, CancellationToken cancellationToken) =>
        userService.LockAsync(request, cancellationToken);
}