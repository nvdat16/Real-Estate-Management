using MediatR;

namespace Bds.Service.Identity.UseCases.Users.Commands;

public sealed record UnlockUserCommand(Guid UserId) : IRequest;