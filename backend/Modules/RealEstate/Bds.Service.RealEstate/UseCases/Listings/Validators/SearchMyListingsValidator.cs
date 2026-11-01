using Bds.BuildingBlocks.Application.Validation;
using Bds.Domain.RealEstate.Enums;
using Bds.Service.RealEstate.Helpers;
using Bds.Service.RealEstate.UseCases.Listings.Queries;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Listings.Validators;

public sealed class SearchMyListingsValidator : AbstractValidator<SearchMyListingsQuery>
{
    public SearchMyListingsValidator()
    {
        this.AddPagingRules("price", "createdAt");

        RuleFor(x => x.Status)
            .Must(EnumNames.IsDefinedName<ListingStatus>)
            .WithMessage("Trạng thái phải là Draft, PendingReview, Approved, Rejected hoặc Closed.")
            .When(x => x.Status is not null);

        RuleFor(x => x.Type)
            .Must(EnumNames.IsDefinedName<ListingType>)
            .WithMessage("Loại tin phải là Sale (bán) hoặc Rent (cho thuê).")
            .When(x => x.Type is not null);
    }
}
