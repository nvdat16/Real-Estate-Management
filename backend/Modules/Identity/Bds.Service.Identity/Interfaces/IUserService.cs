using Bds.Model.Dto.Identity.Responses;
using Bds.Service.Identity.UseCases.Users.Commands;

namespace Bds.Service.Identity.Interfaces;

public interface IUserService
{
    Task<UserResponse> CreateAsync(CreateUserCommand command, CancellationToken cancellationToken);

    Task LockAsync(LockUserCommand command, CancellationToken cancellationToken);

    Task UnlockAsync(UnlockUserCommand command, CancellationToken cancellationToken);
}