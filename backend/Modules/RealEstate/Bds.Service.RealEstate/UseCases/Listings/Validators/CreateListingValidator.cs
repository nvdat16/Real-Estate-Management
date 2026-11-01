using Bds.Service.RealEstate.UseCases.Listings.Commands;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Listings.Validators;

public sealed class CreateListingValidator : AbstractValidator<CreateListingCommand>
{
    public CreateListingValidator()
    {
        RuleFor(x => x.PropertyId).NotEmpty().WithMessage("Vui lòng chọn căn hộ.");

        this.AddListingContentRules();
    }
}
