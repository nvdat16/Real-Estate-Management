using Bds.BuildingBlocks.Application.Exceptions;
using Bds.Domain.Identity.Entities;
using Bds.Infrastructure.Identity.Interfaces;
using Bds.Model.Dto.Identity.Responses;
using Bds.Service.Identity.Interfaces;
using Bds.Service.Identity.UseCases.Users;
using Bds.Service.Identity.UseCases.Users.Commands;

namespace Bds.Service.Identity.Services;

public sealed class UserService(
    IUserRepository userRepository,
    IRoleRepository roleRepository,
    IPasswordHasher passwordHasher,
    IIdentityUnitOfWork unitOfWork) : IUserService
{
    public async Task<UserResponse> CreateAsync(CreateUserCommand command, CancellationToken cancellationToken)
    {
        var email = User.NormalizeEmail(command.Email);
        if (await userRepository.ExistsByEmailAsync(email, cancellationToken))
        {
            throw AppException.Conflict("Email đã được sử dụng");
        }

        var role = await roleRepository.GetByNameAsync(command.Role, cancellationToken)
            ?? throw AppException.NotFound("Không tìm thấy vai trò");

        var user = User.Create(email, passwordHasher.Hash(command.Password), command.FullName, command.PhoneNumber, role);
        userRepository.Add(user);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return UserMapping.ToResponse(user);
    }

    public async Task LockAsync(LockUserCommand command, CancellationToken cancellationToken)
    {
        if (command.UserId == command.CurrentUserId)
        {
            throw AppException.BusinessRule("Không thể tự khóa tài khoản của mình.");
        }

        var user = await userRepository.GetByIdAsync(command.UserId, cancellationToken)
            ?? throw AppException.NotFound("Không tìm thấy người dùng.");

        user.Lock();
        await unitOfWork.SaveChangesAsync(cancellationToken);
    }

    public async Task UnlockAsync(UnlockUserCommand command, CancellationToken cancellationToken)
    {
        var user = await userRepository.GetByIdAsync(command.UserId, cancellationToken)
            ?? throw AppException.NotFound("Không tìm thấy người dùng.");

        user.Unlock();
        await unitOfWork.SaveChangesAsync(cancellationToken);
    }
}