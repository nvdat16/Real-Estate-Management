using MediatR;

namespace Bds.Service.Identity.UseCases.Users.Commands;

public sealed record LockUserCommand(Guid UserId, Guid CurrentUserId) : IRequest;