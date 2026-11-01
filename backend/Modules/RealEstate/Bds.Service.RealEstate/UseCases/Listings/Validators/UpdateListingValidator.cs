using Bds.Service.RealEstate.UseCases.Listings.Commands;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Listings.Validators;

public sealed class UpdateListingValidator : AbstractValidator<UpdateListingCommand>
{
    public UpdateListingValidator()
    {
        this.AddListingContentRules();
    }
}
