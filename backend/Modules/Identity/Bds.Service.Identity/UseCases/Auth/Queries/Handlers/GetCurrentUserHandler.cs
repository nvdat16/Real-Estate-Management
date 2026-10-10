using Bds.Model.Dto.Identity.Responses;
using Bds.Service.Identity.Interfaces;
using MediatR;

namespace Bds.Service.Identity.UseCases.Auth.Queries.Handlers;

public sealed class GetCurrentUserHandler(IAuthService authService) 
    : IRequestHandler<GetCurrentUserQuery, UserResponse>
{
    public Task<UserResponse> Handle(GetCurrentUserQuery request, CancellationToken cancellationToken) =>
        authService.GetCurrentUserAsync(request, cancellationToken);
}