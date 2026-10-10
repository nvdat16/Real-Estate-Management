using Bds.Model.Dto.Identity.Responses;
using Bds.Service.Identity.UseCases.Auth.Commands;
using Bds.Service.Identity.UseCases.Auth.Queries;

namespace Bds.Service.Identity.Interfaces;

public interface IAuthService
{
    Task<UserResponse> RegisterAsync(RegisterCommand command, CancellationToken cancellationToken);

    Task<AuthResponse> LoginAsync(LoginCommand command, CancellationToken cancellationToken);

    Task<UserResponse> GetCurrentUserAsync(GetCurrentUserQuery query, CancellationToken cancellationToken);
}