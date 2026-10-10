using Bds.Service.Identity.UseCases.Auth.Commands;
using FluentValidation;

namespace Bds.Service.Identity.UseCases.Auth.Validators;

public sealed class LoginValidator : AbstractValidator<LoginCommand>
{
    public LoginValidator()
    {
        RuleFor(x => x.Email).NotEmpty().WithMessage("Email không được để trống.");
        RuleFor(x => x.Password).NotEmpty().WithMessage("Mật khẩu không được để trống.");
    }
}