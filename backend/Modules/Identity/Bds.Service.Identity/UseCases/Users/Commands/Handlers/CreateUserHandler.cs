using Bds.Model.Dto.Identity.Responses;
using Bds.Service.Identity.Interfaces;
using MediatR;

namespace Bds.Service.Identity.UseCases.Users.Commands.Handlers;

public sealed class CreateUserHandler(IUserService userService) :
    IRequestHandler<CreateUserCommand, UserResponse>
{
    public Task<UserResponse> Handle(CreateUserCommand request, CancellationToken cancellationToken) =>
        userService.CreateAsync(request, cancellationToken);
} 