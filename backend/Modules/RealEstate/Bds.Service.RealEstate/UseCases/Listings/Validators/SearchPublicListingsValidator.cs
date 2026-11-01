using Bds.BuildingBlocks.Application.Validation;
using Bds.Domain.RealEstate.Enums;
using Bds.Service.RealEstate.Helpers;
using Bds.Service.RealEstate.UseCases.Listings.Queries;
using FluentValidation;

namespace Bds.Service.RealEstate.UseCases.Listings.Validators;

public sealed class SearchPublicListingsValidator : AbstractValidator<SearchPublicListingsQuery>
{
    public SearchPublicListingsValidator()
    {
        this.AddPagingRules("price", "area", "createdAt");

        RuleFor(x => x.Type)
            .Must(EnumNames.IsDefinedName<ListingType>)
            .WithMessage("Loại tin phải là Sale (bán) hoặc Rent (cho thuê).")
            .When(x => x.Type is not null);

        // BR-05: sale prices (whole unit) and rent prices (per month) must never share one price range.
        RuleFor(x => x.Type)
            .NotEmpty()
            .WithMessage("Vui lòng chọn loại tin (bán hoặc thuê) khi lọc theo giá.")
            .When(x => x.MinPrice is not null || x.MaxPrice is not null);

        RuleFor(x => x.MinPrice).GreaterThanOrEqualTo(0).WithMessage("Giá tối thiểu không được âm.");
        RuleFor(x => x.MaxPrice)
            .GreaterThanOrEqualTo(x => x.MinPrice).WithMessage("Giá tối đa phải lớn hơn hoặc bằng giá tối thiểu.")
            .When(x => x.MinPrice is not null && x.MaxPrice is not null);

        RuleFor(x => x.MinArea).GreaterThanOrEqualTo(0).WithMessage("Diện tích tối thiểu không được âm.");
        RuleFor(x => x.MaxArea)
            .GreaterThanOrEqualTo(x => x.MinArea).WithMessage("Diện tích tối đa phải lớn hơn hoặc bằng diện tích tối thiểu.")
            .When(x => x.MinArea is not null && x.MaxArea is not null);

        RuleFor(x => x.Bedrooms).InclusiveBetween(0, 20).WithMessage("Số phòng ngủ phải từ 0 đến 20.");
    }
}
