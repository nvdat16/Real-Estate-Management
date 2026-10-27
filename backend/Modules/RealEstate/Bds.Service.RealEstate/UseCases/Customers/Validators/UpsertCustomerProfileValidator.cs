using Bds.Service.RealEstate.UseCases.Customers.Commands;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Customers.Validators;

public sealed class UpsertCustomerProfileValidator : AbstractValidator<UpsertCustomerProfileCommand>
{
    public UpsertCustomerProfileValidator()
    {
        RuleFor(x => x.FullName)
            .NotEmpty().WithMessage("Họ tên không được để trống.")
            .MaximumLength(200).WithMessage("Họ tên tối đa 200 ký tự.");

        RuleFor(x => x.PhoneNumber)
            .NotEmpty().WithMessage("Số điện thoại không được để trống.")
            .Matches(@"^0\d{9}$").WithMessage("Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0.");

        // A customer signs contracts, so the profile must belong to an adult.
        RuleFor(x => x.DateOfBirth)
            .Must(d => IsAdult(d!.Value, DateOnly.FromDateTime(DateTime.UtcNow)))
            .WithMessage("Khách hàng phải đủ 18 tuổi.")
            .Must(d => d!.Value.Year >= 1900)
            .WithMessage("Ngày sinh không hợp lệ.")
            .When(x => x.DateOfBirth is not null);

        RuleFor(x => x.Address).MaximumLength(300).WithMessage("Địa chỉ tối đa 300 ký tự.");
    }

    private static bool IsAdult(DateOnly dateOfBirth, DateOnly today) => dateOfBirth.AddYears(18) <= today;
}
