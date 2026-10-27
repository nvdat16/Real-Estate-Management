using Bds.Service.RealEstate.UseCases.Agents.Commands;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Agents.Validators;

public sealed class UpsertAgentProfileValidator : AbstractValidator<UpsertAgentProfileCommand>
{
    public UpsertAgentProfileValidator()
    {
        RuleFor(x => x.FullName)
            .NotEmpty().WithMessage("Họ tên không được để trống.")
            .MaximumLength(200).WithMessage("Họ tên tối đa 200 ký tự.");

        RuleFor(x => x.PhoneNumber)
            .NotEmpty().WithMessage("Số điện thoại không được để trống.")
            .Matches(@"^0\d{9}$").WithMessage("Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0.");

        RuleFor(x => x.LicenseNumber)
            .MaximumLength(50).WithMessage("Số chứng chỉ hành nghề tối đa 50 ký tự.")
            .Matches("^[A-Za-z0-9/-]+$").WithMessage("Số chứng chỉ hành nghề chỉ gồm chữ, số, dấu gạch ngang và gạch chéo.")
            .When(x => !string.IsNullOrWhiteSpace(x.LicenseNumber));
    }
}
