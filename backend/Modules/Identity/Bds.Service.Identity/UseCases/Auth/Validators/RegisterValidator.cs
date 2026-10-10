using Bds.Service.Identity.UseCases.Auth.Commands;
using FluentValidation;

namespace Bds.Service.Identity.UseCases.Auth.Validators;

public sealed class RegisterValidator : AbstractValidator<RegisterCommand>
{
    public RegisterValidator()
    {
        RuleFor(x => x.Email)
            .NotEmpty().WithMessage("Email không được để trống.")
            .EmailAddress().WithMessage("Email không hợp lệ.")
            .MaximumLength(256).WithMessage("Email tối đa 256 ký tự.");

        RuleFor(x => x.Password)
            .NotEmpty().WithMessage("Mật khẩu không được để trống.")
            .MinimumLength(8).WithMessage("Mật khẩu tối thiểu 8 ký tự.")
            .MaximumLength(128).WithMessage("Mật khẩu tối đa 128 ký tự.")
            .Matches("[A-Z]").WithMessage("Mật khẩu phải có ít nhất một chữ hoa.")
            .Matches("[a-z]").WithMessage("Mật khẩu phải có ít nhất một chữ thường.")
            .Matches("[0-9]").WithMessage("Mật khẩu phải có ít nhất một chữ số.");

        RuleFor(x => x.FullName)
            .NotEmpty().WithMessage("Họ tên không được để trống.")
            .MaximumLength(200).WithMessage("Họ tên tối đa 200 ký tự.");

        RuleFor(x => x.PhoneNumber)
            .Matches(@"^0\d{9}$").WithMessage("Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0.")
            .When(x => !string.IsNullOrWhiteSpace(x.PhoneNumber));
    }
}