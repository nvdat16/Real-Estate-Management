using Bds.BuildingBlocks.Application.Exceptions;
using Bds.Domain.Identity.Constants;
using Bds.Domain.Identity.Entities;
using Bds.Infrastructure.Identity.Interfaces;
using Bds.Model.Dto.Identity.Responses;
using Bds.Service.Identity.Interfaces;
using Bds.Service.Identity.UseCases.Auth.Commands;
using Bds.Service.Identity.UseCases.Auth.Queries;
using Bds.Service.Identity.UseCases.Users;

namespace Bds.Service.Identity.Services;

public sealed class AuthService(
    IUserRepository userRepository,
    IRoleRepository roleRepository,
    IPasswordHasher passwordHasher,
    IJwtTokenGenerator tokenGenerator,
    IIdentityUnitOfWork unitOfWork) : IAuthService
{
    public async Task<UserResponse> RegisterAsync(RegisterCommand command, CancellationToken cancellationToken)
    {
        var email = User.NormalizeEmail(command.Email);

        if (await userRepository.ExistsByEmailAsync(email, cancellationToken))
        {
            throw AppException.Conflict("Email đã được sử dụng");
        }

        var role = await roleRepository.GetByNameAsync(RoleNames.Customer, cancellationToken)
            ?? throw new InvalidOperationException($"Role '{RoleNames.Customer}' has not been seeded.");

        var user = User.Create(email, passwordHasher.Hash(command.Password), command.FullName, command.PhoneNumber, role);

        userRepository.Add(user);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        return UserMapping.ToResponse(user);
    }

    public async Task<AuthResponse> LoginAsync(LoginCommand command, CancellationToken cancellationToken)
    {
        var user = await userRepository.GetByEmailAsync(User.NormalizeEmail(command.Email), cancellationToken);

        if (user is null || !passwordHasher.Verify(user.PasswordHash, command.Password))
        {
            throw AppException.Unauthorized("Email hoặc mật khẩu không đúng");
        }

        if (user.IsLocked)
        {
            throw AppException.Forbidden("Tài khoản đã bị khoá");
        }

        user.RecordLogin(DateTime.UtcNow);
        await unitOfWork.SaveChangesAsync(cancellationToken);

        var (token, expiresAt) = tokenGenerator.Generate(user);

        return new AuthResponse(token, expiresAt, UserMapping.ToResponse(user));
    }

    public async Task<UserResponse> GetCurrentUserAsync(GetCurrentUserQuery query, CancellationToken cancellationToken)
    {
        var user = await userRepository.GetByIdAsync(query.UserId, cancellationToken)
            ?? throw AppException.NotFound("Không tìm thấy người dùng");

        return UserMapping.ToResponse(user);
    }
}