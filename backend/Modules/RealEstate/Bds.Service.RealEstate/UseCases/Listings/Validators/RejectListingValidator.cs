using Bds.Service.RealEstate.UseCases.Listings.Commands;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Listings.Validators;

public sealed class RejectListingValidator : AbstractValidator<RejectListingCommand>
{
    public RejectListingValidator()
    {
        RuleFor(x => x.Reason)
            .NotEmpty().WithMessage("Vui lòng nhập lý do từ chối.")
            .MaximumLength(500).WithMessage("Lý do từ chối tối đa 500 ký tự.");
    }
}
